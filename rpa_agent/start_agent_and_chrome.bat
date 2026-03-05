@echo off
title Start Smart Pricing RPA Agent ^& Chrome
chcp 65001 > nul

echo ============================================================
echo 1) Starting Chrome with Remote Debugging Enabled...
echo ============================================================
echo We will launch Google Chrome to listen on port 9222.
echo Please leave this command window open while working!

set CHROME_EXE=""

:: Find Chrome without complex FOR loops that break batch scripts
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE="%ProgramFiles%\Google\Chrome\Application\chrome.exe"
    goto :FOUND_CHROME
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE="%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    goto :FOUND_CHROME
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set CHROME_EXE="%LocalAppData%\Google\Chrome\Application\chrome.exe"
    goto :FOUND_CHROME
)

:FOUND_CHROME
if %CHROME_EXE%=="" (
    echo [ERROR] Google Chrome was not found on this system!
    echo Please install Chrome or check the installation path.
    pause
    exit /b
)

echo [OK] Found Chrome at: %CHROME_EXE%
echo Launching...

:: Create a dedicated User Data Directory for RPA Chrome to avoid profile locks
set CHROME_USER_DATA="%TEMP%\chrome_rpa_profile"
if not exist %CHROME_USER_DATA% mkdir %CHROME_USER_DATA%

:: Close any existing Chrome processes to ensure the debugging port binds correctly
echo Closing existing Chrome instances...
taskkill /F /IM chrome.exe /T >nul 2>&1
timeout /t 2 >nul

:: Start Chrome in background with debugging port and dedicated profile
:: --no-first-run prevents the welcome screen
:: --no-default-browser-check prevents annoying popups
echo Launching Chrome with dedicated RPA profile...
start "" %CHROME_EXE% --remote-debugging-port=9222 --user-data-dir=%CHROME_USER_DATA% --no-first-run --no-default-browser-check
echo [OK] Chrome started on port 9222

:: Give Chrome a moment to open
timeout /t 2 >nul

echo.
echo ============================================================
echo 2) Starting the Local RPA Agent...
echo ============================================================
echo We will start the background Agent to listen for web requests.

:: Look for the PyInstaller compiled EXE
if exist "rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe
    start "RPA Agent" cmd /k "rpa_agent.exe"
    goto :AGENT_STARTED
)

:: Look for the PyInstaller compiled EXE inside dist directory
if exist "dist\rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe in dist folder
    start "RPA Agent" cmd /k "dist\rpa_agent.exe"
    goto :AGENT_STARTED
)

:: Fallback for Developers (Run Python directly)
python --version >nul 2>&1
if not errorlevel 1 (
    if exist "rpa_agent.py" (
        echo [INFO] No .exe found, but Python is installed. Running raw script...
        start "RPA Agent" cmd /k "python rpa_agent.py"
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
