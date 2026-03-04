@echo off
echo ==================================================
echo   RUN RPA CLIENT
echo ==================================================
echo.

REM Check if Chrome is running
tasklist /FI "IMAGENAME eq chrome.exe" 2^>NUL | find /I /N "chrome.exe"^>NUL
if "%ERRORLEVEL%"=="1" (
    echo [ERROR] Chrome is not running!
    echo Please run start_chrome_debug.bat first
    echo.
    pause
    exit /b 1
)

REM Check if port 9222 is open
netstat -ano | findstr :9222 ^>nul
if "%ERRORLEVEL%"=="1" (
    echo [ERROR] Chrome debug port 9222 is not open!
    echo Please run start_chrome_debug.bat first
    echo.
    pause
    exit /b 1
)

echo [OK] Chrome is running with debug mode
echo.

REM Get quote code from user
set /p QUOTE_CODE="Enter Quote Code (e.g., TRQT): "
if "%QUOTE_CODE%"=="" (
    echo [ERROR] Quote code is required
    pause
    exit /b 1
)

echo.
echo Running RPA for quote: %QUOTE_CODE%
echo.

cd rpa_client
rpa_client.exe %QUOTE_CODE%
cd ..

echo.
echo ==================================================
echo   RPA COMPLETE
echo ==================================================
echo.
pause
