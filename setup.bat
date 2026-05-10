@echo off
echo ============================================================
echo  AI-Based Crop Damage Assessment - Setup Script (Windows)
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment
echo [1/4] Creating Python virtual environment...
cd /d "%~dp0backend"
if not exist "venv" (
    python -m venv venv
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

:: Activate and install dependencies
echo [2/4] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Go back to project root
cd /d "%~dp0"

echo [3/4] Setup complete!
echo.
echo ============================================================
echo  To start the server, run:
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo ============================================================
echo.

:: Start server
echo [4/4] Starting Flask server...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python app.py

pause
