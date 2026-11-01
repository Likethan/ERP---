# CampusOS Local Development Orchestrator for Windows PowerShell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CampusOS Local Development Startup   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$CurrentDir = Get-Location

# Check Python
Write-Host "`n[1/3] Checking Python virtual environment..." -ForegroundColor Yellow
$VenvPython = Join-Path $CurrentDir "apps\api\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment in apps/api/.venv..." -ForegroundColor Gray
    python -m venv "$CurrentDir\apps\api\.venv"
    & "$CurrentDir\apps\api\.venv\Scripts\pip.exe" install -r "$CurrentDir\apps\api\requirements-dev.txt"
}

# Check Frontend Node Modules
Write-Host "`n[2/3] Checking Node.js dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "$CurrentDir\node_modules")) {
    Write-Host "Installing npm workspaces dependencies..." -ForegroundColor Gray
    npm install
}

# Start Concurrent Services in a Single Unified Terminal Window
Write-Host "`n[3/3] Launching Backend API (:8000) and Frontend Web (:3000) together..." -ForegroundColor Green
node "$CurrentDir\scripts\dev.mjs"
