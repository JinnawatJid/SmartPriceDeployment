@echo off
title Start Smart Pricing RPA Agent ^& Chrome
chcp 65001 > nul

echo ============================================================
echo 1) Starting Chrome with Remote Debugging Enabled...
echo ============================================================

:: ============================
:: FIND CHROME
:: ============================
set CHROME_EXE=""

if exist "%~dp0browser\chrome\chrome.exe" (
    set CHROME_EXE="%~dp0browser\chrome\chrome.exe"
)

if %CHROME_EXE%=="" (
    echo [ERROR] Chrome not found!
    pause
    exit /b
)

echo [OK] Found Chrome: %CHROME_EXE%

:: ============================
:: SET RPA PROFILE
:: ============================
set CHROME_USER_DATA=%TEMP%\chrome_rpa_profile

if not exist "%CHROME_USER_DATA%" (
    echo Creating RPA profile...
    mkdir "%CHROME_USER_DATA%"
)

set PROFILE=%CHROME_USER_DATA%\Default

:: ============================
:: 🔥 CLEAR CACHE ONLY
:: ============================
echo Clearing cache...

if exist "%PROFILE%\Cache" rmdir /s /q "%PROFILE%\Cache"
if exist "%PROFILE%\Code Cache" rmdir /s /q "%PROFILE%\Code Cache"
if exist "%PROFILE%\GPUCache" rmdir /s /q "%PROFILE%\GPUCache"

:: optional: clear history
if exist "%PROFILE%\History" del /f /q "%PROFILE%\History"

echo [OK] Cache cleared (password safe)

:: ============================
:: 🔥 CLEAR OLD TABS (SESSION)
:: ============================
echo Clearing old tabs/session...

:: สำหรับ Chrome เวอร์ชันเก่า
del /f /q "%PROFILE%\Current Session" >nul 2>&1
del /f /q "%PROFILE%\Current Tabs" >nul 2>&1
del /f /q "%PROFILE%\Last Session" >nul 2>&1
del /f /q "%PROFILE%\Last Tabs" >nul 2>&1

:: สำหรับ Chrome เวอร์ชันใหม่ (ลบโฟลเดอร์ Sessions ทิ้ง)
if exist "%PROFILE%\Sessions" rmdir /s /q "%PROFILE%\Sessions"

echo [OK] Old tabs cleared
:: ============================
:: CLOSE OLD CHROME (PORT 9222)
:: ============================
echo Closing old Chrome debug instances...
wmic process where "name='chrome.exe' and CommandLine like '%%9222%%'" delete >nul 2>&1
timeout /t 2 >nul

:: ============================
:: 🚀 LAUNCH CHROME
:: ============================
echo Launching Chrome...

start "" %CHROME_EXE% ^
--remote-debugging-port=9222 ^
--user-data-dir="%CHROME_USER_DATA%" ^
--restore-last-session=0 ^
--no-first-run ^
--no-default-browser-check ^
--disable-features=PrivateNetworkAccessSendPreflights ^
--disable-web-security ^
--allow-running-insecure-content ^
--disk-cache-size=0 ^
--media-cache-size=0 ^
--disable-application-cache ^
"http://192.192.0.37:53683/hub" ^ "http://192.192.0.6:8080/BC23TNGLIV/"


echo [OK] Chrome started (clean + no old tabs)

timeout /t 2 >nul

:: ============================================================
echo.
echo 2) Starting the Local RPA Agent...
echo ============================================================

:: ============================
:: START RPA AGENT
:: ============================

if exist "%~dp0rpa_agent.exe" (
    echo [OK] Found rpa_agent.exe
    start "RPA Agent" cmd /k "%~dp0rpa_agent.exe"
    goto :DONE
)

if exist "%~dp0dist\rpa_agent.exe" (
    echo [OK] Found rpa_agent.exe in dist
    start "RPA Agent" cmd /k "%~dp0dist\rpa_agent.exe"
    goto :DONE
)

python --version >nul 2>&1
if not errorlevel 1 (
    if exist "%~dp0rpa_agent.py" (
        echo [INFO] Running Python version...
        start "RPA Agent" cmd /k "python %~dp0rpa_agent.py"
        goto :DONE
    )
)

echo [ERROR] RPA Agent not found!
pause
exit /b

:DONE
echo.
echo ============================================================
echo [SUCCESS] SYSTEM READY
echo ============================================================
echo Chrome: Clean (no cache + no old tabs)
echo RPA Agent: Running
echo Ready for Dynamics 365 BC
echo ============================================================
echo.
pause