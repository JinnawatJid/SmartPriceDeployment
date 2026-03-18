@echo off
title Start Smart Pricing RPA Agent ^& Chrome
chcp 65001 > nul

echo ============================================================
echo 1) Starting Chrome with Remote Debugging Enabled...
echo ============================================================
echo We will launch Google Chrome to listen on port 9222.
echo Please leave this command window open while working!

set CHROME_EXE=""

:: Find the bundled Chrome for Testing
if exist "%~dp0browser\chrome\chrome.exe" (
    set CHROME_EXE="%~dp0browser\chrome\chrome.exe"
    goto :FOUND_CHROME
)

:FOUND_CHROME
if %CHROME_EXE%=="" (
    echo [ERROR] Bundled Chrome was not found!
    echo Please make sure the 'browser' folder is extracted alongside this script.
    pause
    exit /b
)

echo [OK] Found Chrome at: %CHROME_EXE%

:: Detect Python architecture
echo.
echo ============================================================
echo Detecting Python Architecture...
echo ============================================================
python -c "import struct; print('64-bit' if struct.calcsize('P') * 8 == 64 else '32-bit')" > "%TEMP%\python_arch.txt" 2>nul
if errorlevel 1 (
    echo [WARNING] Could not detect Python architecture
) else (
    set /p PYTHON_ARCH=<"%TEMP%\python_arch.txt"
    echo [OK] Python Architecture: %PYTHON_ARCH%
    del "%TEMP%\python_arch.txt"
)
echo.

:: Create a dedicated User Data Directory for RPA Chrome to avoid profile locks
set CHROME_USER_DATA="%TEMP%\chrome_rpa_profile"

:: Clear cookies by removing the profile directory
echo Clearing Chrome cookies and cache...
if exist %CHROME_USER_DATA% (
    rmdir /s /q %CHROME_USER_DATA% >nul 2>&1
    echo [OK] Cleared previous Chrome profile data
)
mkdir %CHROME_USER_DATA%

:: Close any existing Chrome instances running from the bundled folder
echo Closing existing Chrome instances...
wmic process where "name='chrome.exe' and CommandLine like '%%9222%%'" delete >nul 2>&1
timeout /t 2 >nul

:: Start Chrome in background with debugging port and dedicated profile
:: --no-first-run prevents the welcome screen
:: --no-default-browser-check prevents annoying popups
:: --disable-features=BlockInsecurePrivateNetworkRequests disables PNA CORS checks so the frontend can talk to 127.0.0.1
echo Launching Chrome with dedicated RPA profile...
start "" %CHROME_EXE% --remote-debugging-port=9222 --user-data-dir=%CHROME_USER_DATA% --no-first-run --no-default-browser-check --disable-features=BlockInsecurePrivateNetworkRequests "http://192.192.0.37:8000/" "http://192.192.0.6:8080/BC23TNGLIV"
echo [OK] Chrome started on port 9222

:: Give Chrome a moment to open and load the tabs
echo Opening required tabs...
timeout /t 3 >nul
echo [OK] Opened tabs: http://192.192.0.37:8000/ and http://192.192.0.6:8080/BC23TNGLIV

echo.
echo ============================================================
echo 2) Starting the Local RPA Agent...
echo ============================================================
echo We will start the background Agent to listen for web requests.

:: Look for the PyInstaller compiled EXE
if exist "%~dp0rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe
    start "RPA Agent" cmd /k "%~dp0rpa_agent.exe"
    goto :AGENT_STARTED
)

:: Look for the PyInstaller compiled EXE inside dist directory
if exist "%~dp0dist\rpa_agent.exe" (
    echo [OK] Found compiled rpa_agent.exe in dist folder
    start "RPA Agent" cmd /k "%~dp0dist\rpa_agent.exe"
    goto :AGENT_STARTED
)

:: Fallback for Developers (Run Python directly)
python --version >nul 2>&1
if not errorlevel 1 (
    if exist "%~dp0rpa_agent.py" (
        echo [INFO] No .exe found, but Python is installed. Running raw script...
        start "RPA Agent" cmd /k "python %~dp0rpa_agent.py"
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
