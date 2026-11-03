# CampusOS Local PostgreSQL Database Initializer
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  CampusOS PostgreSQL Database Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "This script creates 'campusos_user' and 'campusos_db' in your local PostgreSQL."
Write-Host "When prompted, enter your PostgreSQL 'postgres' superuser password.`n"

$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (-not (Test-Path $psql)) {
    $found = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($found) {
        $psql = $found.Source
    }
}

if (-not (Test-Path $psql)) {
    Write-Host "ERROR: psql.exe not found at $psql" -ForegroundColor Red
    exit 1
}

Write-Host "1. Creating user 'campusos_user'..." -ForegroundColor Yellow
& $psql -U postgres -h localhost -p 5432 -c "DO `$do`$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'campusos_user') THEN CREATE USER campusos_user WITH PASSWORD 'campusos_password' CREATEDB SUPERUSER; ELSE ALTER USER campusos_user WITH PASSWORD 'campusos_password'; END IF; END `$do`$;"

Write-Host "`n2. Creating database 'campusos_db'..." -ForegroundColor Yellow
& $psql -U postgres -h localhost -p 5432 -c "SELECT 'CREATE DATABASE campusos_db OWNER campusos_user' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'campusos_db')\gexec"

Write-Host "`n3. Granting privileges..." -ForegroundColor Yellow
& $psql -U postgres -h localhost -p 5432 -c "GRANT ALL PRIVILEGES ON DATABASE campusos_db TO campusos_user;"

Write-Host "`n4. Testing connection as campusos_user..." -ForegroundColor Yellow
$rootDir = Split-Path -Parent $PSScriptRoot
$pythonBin = Join-Path $rootDir "apps\api\.venv\Scripts\python.exe"

if (Test-Path $pythonBin) {
    & $pythonBin -c "
import asyncio, asyncpg
async def test():
    try:
        conn = await asyncpg.connect('postgresql://campusos_user:campusos_password@localhost:5432/campusos_db')
        print('\x1b[32m[SUCCESS] Successfully connected to campusos_db as campusos_user!\x1b[0m')
        await conn.close()
    except Exception as e:
        print('\x1b[31m[FAILED] Connection test error:\x1b[0m', e)
asyncio.run(test())
"
} else {
    Write-Host "[DONE] Database setup completed." -ForegroundColor Green
}

