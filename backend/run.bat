@echo off
cd /d "%~dp0"
echo Starting PulseRadar Backend with local virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python -m uvicorn app.main:app --reload --port 8000
) else (
    echo Error: Virtual environment not found at .\venv
    echo Please create it first using: python -m venv venv ^&^& pip install -r requirements.txt
    pause
)
