@echo off
setlocal
cd /d "%~dp0"
apps\api\.venv\Scripts\python.exe scripts\import_students.py %*
pause

