@echo off
setlocal enabledelayedexpansion
title Start Smart Pricing RPA Agent ^& Chrome
chcp 65001 > nul

echo ============================================================
echo 1) Starting Chrome with Remote Debugging Enabled...
echo ============================================================
echo We will launch Google Chrome to listen on port 9222.
echo Please leave this command window open while working!

:: Set common paths for Chrome installation
set CHROME_EXE=

:: Try common Chrome installation paths
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe
    goto :FOUND_CHROME
)

if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
    goto :FOUND_CHROME
)

if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe
    goto :FOUND_CHROME
)

:FOUND_CHROME
if "%CHROME_EXE%"=="" (
    echo [ERROR] Google Chrome was not found on this system!
    echo Please install Chrome or check the installation path.
    pause
    exit /b
)

echo [OK] Found Chrome at: %CHROME_EXE%
echo Launching...

:: Close all existing Chrome instances first
echo Closing existing Chrome instances...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 >nul

:: Start Chrome in background with debugging port and open required tabs
start "" "%CHROME_EXE%" --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --user-data-dir="%TEMP%\chrome_rpa_profile" "http://192.192.0.36:8080/BCTNG" "http://192.192.0.37:8000/create?step=6"
echo [OK] Chrome started on port 9222 with BC and Smart Pricing tabs

:: Give Chrome more time to fully start
echo Waiting for Chrome to initialize...
timeout /t 10 >nul

:: Verify Chrome debugging port is listening
echo Verifying Chrome debugging port...
netstat -ano | findstr :9222 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Chrome debugging port 9222 is not listening yet!
    echo [INFO] Waiting a bit more...
    timeout /t 5 >nul
    netstat -ano | findstr :9222 >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Chrome debugging port still not accessible!
        echo [INFO] This might cause RPA to fail. Please check Chrome is running.
    ) else (
        echo [OK] Chrome debugging port is now listening!
    )
) else (
    echo [OK] Chrome debugging port is listening!
)

echo.
echo ============================================================
echo 2) Starting the Local RPA Agent...
echo ============================================================
echo We will start the background Agent to listen for web requests.

:: Look for the PyInstaller compiled EXE
if exist "rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe
    start "RPA Agent" cmd /c "rpa_agent.exe & pause"
    goto :AGENT_STARTED
)

:: Look for the PyInstaller compiled EXE inside dist directory
if exist "dist\rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe in dist folder
    start "RPA Agent" cmd /c "dist\rpa_agent.exe & pause"
    goto :AGENT_STARTED
)

:: Fallback for Developers (Run Python directly)
python --version >nul 2>&1
if not errorlevel 1 (
    if exist "rpa_agent.py" (
        echo [INFO] No .exe found, but Python is installed. Running raw script...
        start "RPA Agent" cmd /c "python rpa_agent.py & pause"
        goto :AGENT_STARTED
    )
)

echo.
echo [ERROR] RPA Agent executable (rpa_agent.exe) not found!
echo Please make sure the .exe is in the same folder as this script.
pause
exit /b

:AGENT_STARTED
echo.
echo ============================================================
echo [SUCCESS] Everything is ready!
echo 1. Chrome is open and ready to receive commands.
echo 2. The RPA Agent is running in a separate window.
echo 3. You can now use "Send to Dynamics 365 BC" on the Web App!
echo ============================================================
echo.
echo NOTE: Do not close the black "RPA Agent" command window.
pause
