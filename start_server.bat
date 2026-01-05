@echo off
setlocal
title Smart Pricing Server

echo ==================================================
echo      SMART PRICING - SERVER LAUNCHER
echo ==================================================

REM 1. Check for GTK3 (Required for WeasyPrint)
echo Checking for GTK3 Runtime...
if not exist "C:\Program Files\GTK3-Runtime Win64\bin\libcairo-2.dll" (
    if not exist "C:\Program Files (x86)\GTK3-Runtime Win64\bin\libcairo-2.dll" (
        echo [WARNING] GTK3 Runtime not found! PDF generation might fail.
        echo Please install GTK3 Runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
        echo.
        pause
    )
)

echo.
echo Starting Application...
echo Open your browser at: http://localhost:8000
echo (Press Ctrl+C to stop)
echo.

cd dist\smart_pricing
smart_pricing.exe

pause
