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

# Start Concurrent Services
Write-Host "`n[3/3] Launching Backend API (:8000) and Frontend Web (:3000)..." -ForegroundColor Green
Write-Host "  - Backend API: http://localhost:8000 (Docs: http://localhost:8000/docs)" -ForegroundColor Gray
Write-Host "  - Frontend Web: http://localhost:3000" -ForegroundColor Gray
Write-Host "  Press Ctrl+C in the respective windows to stop.`n" -ForegroundColor DarkGray

# Start backend in a new process window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\apps\api'; .\.venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"

# Start frontend in this window
Set-Location "$CurrentDir"
npm run dev --workspace=apps/web
