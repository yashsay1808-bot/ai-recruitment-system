@echo off
setlocal enabledelayedexpansion
title AI Recruitment System - Review Demo Launcher
echo =====================================================================
echo    AI-POWERED INTELLIGENT RECRUITMENT SYSTEM (PHASE 2 ATS)
echo               Review Demo Quick Launcher
echo =====================================================================
echo.

:: 1. Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org/ and re-run this file.
    echo.
    pause
    exit /b 1
)

:: 2. Navigate to frontend
cd /d "%~dp0frontend"

:: 3. Check if node_modules exists (in case zip excluded it)
if not exist "node_modules\" (
    echo [SETUP] node_modules not detected. Installing dependencies...
    echo (This takes ~30 seconds on the first run, please wait...)
    echo.
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please run 'npm install' manually inside the 'frontend' folder.
        pause
        exit /b 1
    )
    echo [SETUP] Dependencies installed successfully!
    echo.
)

:: 4. Start Vite Dev Server
echo [1/2] Starting local web application server...
start "" cmd /c "npm run dev"

:: 5. Open browser
echo [2/2] Opening application in default browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173/

echo.
echo =====================================================================
echo    Status: Demo is LIVE at http://localhost:5173/
echo    Guide:  Open REVIEW_READY_GUIDE.md for 5-minute presentation script!
echo =====================================================================
echo.
pause
