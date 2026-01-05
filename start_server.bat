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

if exist smart_pricing.exe (
    smart_pricing.exe
) else (
    if exist dist\smart_pricing\smart_pricing.exe (
        cd dist\smart_pricing
        smart_pricing.exe
    ) else (
        echo [ERROR] Could not find smart_pricing.exe.
        echo Please verify you are running this script from the correct folder.
        pause
    )
)

pause
