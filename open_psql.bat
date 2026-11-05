@echo off
setlocal
echo Opening PostgreSQL Command Line (psql) connected to campusos_db on port 5433...
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -p 5433 -U campusos_user -d campusos_db
pause

