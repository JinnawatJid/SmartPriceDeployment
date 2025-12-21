@echo off
REM start_server.bat
REM Starts the Smart Pricing System

echo Starting Smart Pricing System...

REM Check for GTK3 (WeasyPrint dependency)
if not exist "C:\Program Files\GTK3-Runtime Win64\bin\libgtk-3-0.dll" (
    echo ========================================================
    echo WARNING: GTK3 Runtime not found in default location.
    echo Searching for installer in current directory...

    REM Look for gtk3 installer
    if exist gtk3-runtime*.exe (
        echo Found installer. Launching...
        for %%f in (gtk3-runtime*.exe) do (
            echo Running %%f...
            start /wait %%f
        )
        echo Please restart this script after installation.
        pause
        exit /b
    ) else (
        echo Installer not found. PDF generation might fail.
        echo Please install gtk3-runtime manually.
        echo ========================================================
    )
)

echo.
echo Please do not close this window while using the application.
echo Access the application at http://localhost:3200
echo.

REM Open Browser
start http://localhost:3200

REM Run the application
REM The executable is located in the smart_pricing folder
cd smart_pricing
smart_pricing.exe

REM Pause to keep the window open if the server crashes
echo.
echo ========================================================
echo Server has stopped.
echo If this was unexpected, please share the error message above.
echo ========================================================
pause
