@echo off
setlocal
cd /d "%~dp0"
backend\.venv\Scripts\python.exe scripts\import_students.py %*
pause

