@echo off
setlocal
cd /d "%~dp0"
apps\api\.venv\Scripts\python.exe scripts\list_students.py
pause

