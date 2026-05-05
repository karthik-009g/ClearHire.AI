$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$statePath = Join-Path $root ".run\app-processes.json"

function Stop-IfRunning([int]$ProcessId) {
    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        Write-Host "Stopping $($proc.ProcessName) ($ProcessId)" -ForegroundColor Yellow
        Stop-Process -Id $ProcessId -Force
    }
    catch {
        Write-Host "Process $ProcessId is not running"
    }
}

if (Test-Path $statePath) {
    $state = Get-Content -Path $statePath -Raw | ConvertFrom-Json

    if ($state.backend_pid) {
        Stop-IfRunning -ProcessId ([int]$state.backend_pid)
    }
    if ($state.frontend_pid) {
        Stop-IfRunning -ProcessId ([int]$state.frontend_pid)
    }
}

foreach ($port in 8000, 3000) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        try {
            $proc = Get-Process -Id $listener.OwningProcess -ErrorAction Stop
            Write-Host "Stopping $($proc.ProcessName) ($($proc.Id)) on port $port" -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
        }
        catch {
            # ignore
        }
    }
}

Write-Host "All known app processes stopped." -ForegroundColor Green
