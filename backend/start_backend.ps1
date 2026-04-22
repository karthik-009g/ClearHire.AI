$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$candidates = @(
	(Join-Path $PSScriptRoot "..\..\.venv\Scripts\python.exe"),
	(Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"),
	(Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
	"C:/Users/gubba/AppData/Local/Microsoft/WindowsApps/python3.11.exe"
)

$python = $null
foreach ($candidate in $candidates) {
	if (Test-Path $candidate) {
		$python = $candidate
		break
	}
}

if (-not $python) {
	throw "Python executable not found. Create/activate a virtual environment first."
}

Write-Host "Using Python: $python"

Write-Host "Applying migrations..."
& $python -m alembic upgrade head

Write-Host "Starting backend on http://127.0.0.1:8000"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
