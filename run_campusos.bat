@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo   Starting CampusOS Unified Full-Stack System
echo   Frontend Web:         http://localhost:3000
echo   Backend API:          http://localhost:8000
echo   API Docs:             http://localhost:8000/docs
echo   Database Visualizer:  http://localhost:5434
echo ===================================================
echo.
echo Launching services... The browser will open automatically when ready.
echo.
npm run dev
pause
