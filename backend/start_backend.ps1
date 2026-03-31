$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = "C:/Users/gubba/AppData/Local/Microsoft/WindowsApps/python3.11.exe"

Write-Host "Applying migrations..."
& $python -m alembic upgrade head

Write-Host "Starting backend on http://127.0.0.1:8000"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
