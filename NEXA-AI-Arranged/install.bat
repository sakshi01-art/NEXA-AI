@echo off
echo ========================================
echo   NEXA AI - Installation Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Install Node.js 18+
    pause
    exit /b 1
)

echo [1/6] Creating directories...
mkdir data\memory data\twins data\meetings data\sessions temp logs plugins 2>nul
echo Done.

echo [2/6] Setting up Python environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Done.

echo [3/6] Installing Python dependencies...
pip install -r requirements.txt
echo Done.

echo [4/6] Installing Playwright browsers...
playwright install chromium
echo Done.

echo [5/6] Installing frontend dependencies...
cd frontend
npm install
cd ..
echo Done.

echo [6/6] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo Created .env - Please add your API keys!
) else (
    echo .env already exists
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run start.bat to launch NEXA AI
echo.
pause
