@echo off
REM Start Chrome with remote debugging enabled
REM This allows Playwright to connect to existing Chrome instance

echo Starting Chrome with remote debugging on port 9222...
echo.

REM Close existing Chrome instances first (optional)
REM taskkill /F /IM chrome.exe 2>nul

REM Start Chrome with remote debugging and open both tabs
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug-profile" "http://192.192.0.36:8080/BCTNG" "http://192.192.0.37:8000/"

echo.
echo Chrome started with remote debugging enabled!
echo You can now run the RPA script: python rpa_click_new_quote.py
echo.
pause
