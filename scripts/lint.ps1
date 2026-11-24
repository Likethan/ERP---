# CampusOS Linting & Code Quality Checker for Windows PowerShell
Write-Host "Running code quality checks across CampusOS..." -ForegroundColor Cyan

$CurrentDir = Get-Location

# Frontend checks
Write-Host "`n[1/3] Checking Frontend TypeScript & Lint..." -ForegroundColor Yellow
npm run typecheck --workspace=frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend type check failed!" -ForegroundColor Red
    exit 1
}

# Shared packages check
Write-Host "`n[2/3] Checking Shared Packages TypeScript..." -ForegroundColor Yellow
npm run typecheck --workspace=packages/types
if ($LASTEXITCODE -ne 0) {
    Write-Host "Shared packages type check failed!" -ForegroundColor Red
    exit 1
}

# Backend checks
Write-Host "`n[3/3] Checking Backend Python Lint..." -ForegroundColor Yellow
$VenvPython = Join-Path $CurrentDir "backend\.venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & "$CurrentDir\backend\.venv\Scripts\ruff.exe" check "$CurrentDir\backend"
} else {
    Write-Host "Python virtual environment not found in backend/.venv. Skipping ruff check." -ForegroundColor DarkGray
}

Write-Host "`nAll code quality checks passed successfully!" -ForegroundColor Green
