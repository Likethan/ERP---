@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo   CampusOS Database Web Visualizer
echo   URL: http://localhost:5434
echo ===================================================
backend\.venv\Scripts\python.exe scripts\db_viewer.py
pause
