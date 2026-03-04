@echo off
echo ==================================================
echo   START CHROME WITH DEBUG MODE
echo ==================================================
echo.
echo Starting Chrome with remote debugging...
echo Chrome will listen on 0.0.0.0:9222
echo.

REM Close existing Chrome instances
taskkill /F /IM chrome.exe 2^>nul
timeout /t 2 /nobreak ^>nul

REM Start Chrome with debug mode
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-debugging-address=0.0.0.0 ^
  --remote-allow-origins=* ^
  --user-data-dir="%TEMP%\chrome-debug-profile" ^
  "http://192.192.0.36:8080/BCTNG" ^
  "http://192.192.0.37:8000/"

echo.
echo Chrome started!
echo Tab 1: Dynamics 365 BC
echo Tab 2: Smart Pricing System
echo.
echo You can now run rpa_client.exe
echo.
pause
