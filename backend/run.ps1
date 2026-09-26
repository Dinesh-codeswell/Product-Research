# PulseRadar Backend PowerShell Launcher
Set-Location $PSScriptRoot

if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "Starting PulseRadar Backend using .\venv\Scripts\python.exe..." -ForegroundColor Cyan
    & ".\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
} else {
    Write-Error "Virtual environment not found at .\venv. Please create it first: python -m venv venv; .\venv\Scripts\pip install -r requirements.txt"
}
