@echo off
REM Start Chrome with remote debugging enabled
REM This allows RPA from Server to connect to Chrome on Client

echo Starting Chrome with remote debugging on port 9222...
echo IMPORTANT: Chrome will listen on 0.0.0.0 (accessible from network)
echo Make sure firewall allows port 9222
echo.

REM Close existing Chrome instances first (optional)
REM taskkill /F /IM chrome.exe 2>nul

REM Start Chrome with remote debugging
REM --remote-debugging-address=0.0.0.0 allows connections from other machines
REM --remote-allow-origins=* allows RPA from Server to connect
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-debugging-address=0.0.0.0 ^
  --remote-allow-origins=* ^
  --user-data-dir="%TEMP%\chrome-debug-profile" ^
  "http://192.192.0.36:8080/BCTNG" ^
  "http://192.192.0.37:8000/"

echo.
echo Chrome started with remote debugging enabled!
echo Listening on: 0.0.0.0:9222 (accessible from network)
echo Tab 1: Dynamics 365 BC
echo Tab 2: Smart Pricing System (Login)
echo.
echo You can now use RPA from the server (192.192.0.37)
echo.
pause
