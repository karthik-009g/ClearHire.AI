$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = "C:/Users/gubba/AppData/Local/Microsoft/WindowsApps/python3.11.exe"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

Write-Host "Starting Streamlit on http://127.0.0.1:8501"
& $python -m streamlit run app.py --server.port 8501 --server.headless true
