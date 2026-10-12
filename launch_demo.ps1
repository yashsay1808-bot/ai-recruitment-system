# AI-Powered Intelligent Recruitment System - PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   AI-POWERED INTELLIGENT RECRUITMENT SYSTEM (PHASE 2 ATS)" -ForegroundColor Green
Write-Host "              Review Demo Quick Launcher" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js is not installed on this system!" -ForegroundColor Red
    Write-Host "Please download and install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit..."
    exit 1
}

$frontendDir = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendDir

# 2. Check if node_modules exists
$nodeModulesDir = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModulesDir)) {
    Write-Host "[SETUP] node_modules not detected. Installing dependencies (first run only)..." -ForegroundColor Yellow
    Start-Process -FilePath "npm.cmd" -ArgumentList "install" -Wait -NoNewWindow
    Write-Host "[SETUP] Dependencies installed successfully!" -ForegroundColor Green
}

# 3. Start Vite dev server
Write-Host "[1/2] Starting local web application server..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WindowStyle Minimized

Start-Sleep -Seconds 3

# 4. Open browser
Write-Host "[2/2] Opening browser at http://localhost:5173/..." -ForegroundColor Yellow
Start-Process "http://localhost:5173/"

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "   Demo is LIVE at: http://localhost:5173/" -ForegroundColor White
Write-Host "   Guide: Check REVIEW_READY_GUIDE.md for presentation notes!" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Green
