@echo off
setlocal
cd /d "%~dp0"
echo Starting CampusOS Database Web Visualizer on http://localhost:5434 ...
start http://localhost:5434
apps\api\.venv\Scripts\python.exe scripts\db_viewer.py
pause

