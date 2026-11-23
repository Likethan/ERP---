@echo off
setlocal
cd /d "%~dp0"
backend\.venv\Scripts\python.exe scripts\add_student.py %*
pause

