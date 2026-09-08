@echo off
title NEXA AI Launcher
echo ========================================
echo   NEXA AI - Starting...
echo ========================================

:: Detect Python environment
if exist "..\.venv\Scripts\activate.bat" (
    call ..\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Start backend
echo Starting Backend (FastAPI + WebSocket on port 8000)...
start "NEXA Backend" cmd /k "cd backend && python main.py"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting Frontend (React + Vite on port 3000)...
start "NEXA Frontend" cmd /k "cd frontend && npm.cmd start"

echo.
echo ========================================
echo   NEXA AI is running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ========================================
echo.
pause
