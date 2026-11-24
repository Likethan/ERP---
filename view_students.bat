@echo off
setlocal
cd /d "%~dp0"
backend\.venv\Scripts\python.exe scripts\list_students.py
pause

