@echo off
setlocal
cd /d "%~dp0"
apps\api\.venv\Scripts\python.exe scripts\add_student.py %*
pause

