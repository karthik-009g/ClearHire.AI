param(
    [ValidateSet("streamlit", "next")]
    [string]$Frontend = "streamlit",
    [switch]$SkipInstall,
    [switch]$SkipMigrate,
    [switch]$StartInfra,
    [switch]$ForceRestart,
    [switch]$UseIsolatedVenv
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $root "backend"
$streamlitPath = Join-Path $root "streamlit-client"
$nextPath = Join-Path $root "frontend"
$runDir = Join-Path $root ".run"
$statePath = Join-Path $runDir "app-processes.json"

New-Item -ItemType Directory -Path $runDir -Force | Out-Null

function Write-Step([string]$Message) {
    Write-Host "[start-app] $Message" -ForegroundColor Cyan
}

function Get-PortOwner([int]$Port) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) {
        return $null
    }

    try {
        return Get-Process -Id $listener.OwningProcess -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Stop-PortOwner([int]$Port) {
    $proc = Get-PortOwner -Port $Port
    if ($null -ne $proc) {
        Write-Step "Stopping process $($proc.ProcessName) ($($proc.Id)) on port $Port"
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-BasePython {
    $candidates = @(
        (Join-Path $root "..\.venv\Scripts\python.exe"),
        (Join-Path $root "..\..\.venv\Scripts\python.exe"),
        (Join-Path $root ".venv\Scripts\python.exe"),
        "python"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) {
                return "python"
            }
            continue
        }

        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "No Python executable found. Install Python 3.11+ or create .venv at workspace root."
}

function Ensure-EnvFile([string]$ServicePath) {
    $envPath = Join-Path $ServicePath ".env"
    $envExamplePath = Join-Path $ServicePath ".env.example"

    if ((-not (Test-Path $envPath)) -and (Test-Path $envExamplePath)) {
        Copy-Item -Path $envExamplePath -Destination $envPath
        Write-Step "Created .env from .env.example in $ServicePath"
    }
}

function Ensure-PythonRuntime(
    [string]$ServicePath,
    [string]$RequirementsPath,
    [string]$BasePython,
    [string]$ServiceName,
    [switch]$SkipInstallDeps,
    [switch]$IsolatedVenv
) {
    $runtimePython = $BasePython
    if ($IsolatedVenv) {
        $venvPath = Join-Path $ServicePath ".venv"
        $venvPython = Join-Path $venvPath "Scripts\python.exe"

        if (-not (Test-Path $venvPython)) {
            Write-Step "Creating virtual environment in $ServicePath"
            & $BasePython -m venv $venvPath
        }

        $runtimePython = $venvPython
    }
    else {
        Write-Step "Using shared Python runtime: $runtimePython"
    }

    if (-not $SkipInstallDeps) {
        $stampPath = Join-Path $runDir "$ServiceName.requirements.sha256"

        $currentHash = (Get-FileHash -Path $RequirementsPath -Algorithm SHA256).Hash
        $previousHash = if (Test-Path $stampPath) { (Get-Content -Path $stampPath -Raw).Trim() } else { "" }

        if ($currentHash -ne $previousHash) {
            Write-Step "Installing Python dependencies in $ServicePath"
            & $runtimePython -m pip install --upgrade pip
            & $runtimePython -m pip install -r $RequirementsPath
            Set-Content -Path $stampPath -Value $currentHash -NoNewline
        }
        else {
            Write-Step "Python dependencies unchanged in $ServicePath, skipping install"
        }
    }

    return $runtimePython
}

function Ensure-NodeRuntime([string]$FrontendPath, [switch]$SkipInstallDeps) {
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue

    if (-not $nodeCmd -or -not $npmCmd) {
        throw "Node.js and npm are required for Next frontend. Install Node 18+ first."
    }

    $envLocal = Join-Path $FrontendPath ".env.local"
    $envExample = Join-Path $FrontendPath ".env.example"
    if ((-not (Test-Path $envLocal)) -and (Test-Path $envExample)) {
        Copy-Item -Path $envExample -Destination $envLocal
        Write-Step "Created .env.local from .env.example"
    }

    if ($SkipInstallDeps) {
        return
    }

    $nodeModulesPath = Join-Path $FrontendPath "node_modules"
    $lockPath = Join-Path $FrontendPath "package-lock.json"
    $stampDir = Join-Path $FrontendPath ".run"
    $stampPath = Join-Path $stampDir "package-lock.sha256"
    New-Item -ItemType Directory -Path $stampDir -Force | Out-Null

    $currentHash = if (Test-Path $lockPath) { (Get-FileHash -Path $lockPath -Algorithm SHA256).Hash } else { "" }
    $previousHash = if (Test-Path $stampPath) { (Get-Content -Path $stampPath -Raw).Trim() } else { "" }

    if ((-not (Test-Path $nodeModulesPath)) -or ($currentHash -ne $previousHash)) {
        Write-Step "Installing Node dependencies in $FrontendPath"
        Push-Location $FrontendPath
        try {
            npm install
        }
        finally {
            Pop-Location
        }
        if ($currentHash) {
            Set-Content -Path $stampPath -Value $currentHash -NoNewline
        }
    }
    else {
        Write-Step "Node dependencies unchanged in $FrontendPath, skipping install"
    }
}

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            # Service not ready yet.
        }
        Start-Sleep -Milliseconds 800
    }
    return $false
}

if ($ForceRestart) {
    Write-Step "Force restart enabled; clearing services on ports 8000, 8501, and 3000"
    Stop-PortOwner -Port 8000
    Stop-PortOwner -Port 8501
    Stop-PortOwner -Port 3000
}

if ($StartInfra) {
    $composePath = Join-Path $root "deployment\docker\docker-compose.yml"
    if (-not (Test-Path $composePath)) {
        throw "Docker compose file not found at $composePath"
    }

    Write-Step "Starting Postgres and Redis via Docker"
    Push-Location (Split-Path -Parent $composePath)
    try {
        docker compose up -d postgres redis
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not start Docker infra. Continuing with existing database/redis configuration."
        }
    }
    finally {
        Pop-Location
    }
}

$basePython = Resolve-BasePython
Ensure-EnvFile -ServicePath $backendPath

$backendPython = Ensure-PythonRuntime `
    -ServicePath $backendPath `
    -RequirementsPath (Join-Path $backendPath "requirements.txt") `
    -BasePython $basePython `
    -ServiceName "backend" `
    -SkipInstallDeps:$SkipInstall `
    -IsolatedVenv:$UseIsolatedVenv

if (-not $SkipMigrate) {
    Write-Step "Applying backend migrations"
    Push-Location $backendPath
    try {
        & $backendPython -m alembic upgrade head
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Step "Skipping backend migrations by request"
}

$backendProcess = $null
if ($null -eq (Get-PortOwner -Port 8000)) {
    Write-Step "Starting backend on http://127.0.0.1:8000"
    $backendCommand = "Set-Location '$backendPath'; & '$backendPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    $backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand -WindowStyle Hidden -PassThru
}
else {
    Write-Step "Backend already running on port 8000"
}

if (Wait-ForHttp -Url "http://127.0.0.1:8000/health" -TimeoutSeconds 45) {
    Write-Step "Backend is healthy"
}
else {
    Write-Warning "Backend health endpoint did not respond in time."
}

$frontendProcess = $null
$frontendUrl = ""

if ($Frontend -eq "streamlit") {
    $streamlitPython = Ensure-PythonRuntime `
        -ServicePath $streamlitPath `
        -RequirementsPath (Join-Path $streamlitPath "requirements.txt") `
        -BasePython $basePython `
        -ServiceName "streamlit-client" `
        -SkipInstallDeps:$SkipInstall `
        -IsolatedVenv:$UseIsolatedVenv

    if ($null -eq (Get-PortOwner -Port 8501)) {
        Write-Step "Starting Streamlit on http://127.0.0.1:8501"
        $streamlitCommand = "Set-Location '$streamlitPath'; & '$streamlitPython' -m streamlit run app.py --server.port 8501 --server.headless true"
        $frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $streamlitCommand -WindowStyle Hidden -PassThru
    }
    else {
        Write-Step "Streamlit already running on port 8501"
    }

    $frontendUrl = "http://127.0.0.1:8501"
    if (-not (Wait-ForHttp -Url $frontendUrl -TimeoutSeconds 45)) {
        Write-Warning "Streamlit did not respond in time."
    }
}
else {
    Ensure-NodeRuntime -FrontendPath $nextPath -SkipInstallDeps:$SkipInstall

    if ($null -eq (Get-PortOwner -Port 3000)) {
        Write-Step "Starting Next frontend on http://127.0.0.1:3000"
        $nextCommand = "Set-Location '$nextPath'; npm run dev"
        $frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $nextCommand -WindowStyle Hidden -PassThru
    }
    else {
        Write-Step "Next frontend already running on port 3000"
    }

    $frontendUrl = "http://127.0.0.1:3000"
    if (-not (Wait-ForHttp -Url $frontendUrl -TimeoutSeconds 60)) {
        Write-Warning "Next frontend did not respond in time."
    }
}

$state = [ordered]@{
    started_at = (Get-Date).ToString("o")
    frontend = $Frontend
    backend_pid = if ($backendProcess) { $backendProcess.Id } else { $null }
    frontend_pid = if ($frontendProcess) { $frontendProcess.Id } else { $null }
    backend_url = "http://127.0.0.1:8000"
    frontend_url = $frontendUrl
}
$state | ConvertTo-Json | Set-Content -Path $statePath

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host "Frontend: $frontendUrl"
Write-Host "State file: $statePath"
