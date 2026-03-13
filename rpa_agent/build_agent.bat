@echo off
setlocal enabledelayedexpansion

title Build Local RPA Agent

REM ตรวจสอบว่าอยู่ในโฟลเดอร์ rpa_agent หรือไม่
if exist "rpa_agent.py" (
    echo [INFO] Running from rpa_agent directory
    set "SCRIPT_DIR=%cd%"
) else if exist "rpa_agent\rpa_agent.py" (
    echo [INFO] Running from parent directory, changing to rpa_agent
    cd rpa_agent
    set "SCRIPT_DIR=%cd%"
) else (
    echo [ERROR] Cannot find rpa_agent.py
    echo Please run this script from the rpa_agent directory or its parent directory
    pause
    exit /b 1
)

echo.
echo ==============================================
echo 1) Checking for Python Installation...
echo ==============================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Check for 32-bit Python explicitly
python -c "import platform; import sys; sys.exit(0) if platform.architecture()[0] == '32bit' else sys.exit(1)"
if errorlevel 1 (
    echo [WARNING] You are not using a 32-bit Python interpreter.
    echo To deploy to 32-bit Windows machines, you MUST use a 32-bit version of Python.
    echo Found:
    python -c "import platform; print(platform.architecture()[0])"
    echo Press any key to continue building anyway, or close this window to stop...
    pause
)

echo.
echo ==============================================
echo 2) Setting up Virtual Environment...
echo ==============================================
echo Removing corrupted or old virtual environment (if any)...
if exist "venv" rmdir /S /Q "venv"

echo Creating fresh virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo ==============================================
echo 3) Installing Dependencies...
echo ==============================================
echo Using verbose output to show build progress (compiling packages may take several minutes)...
pip install -v -r requirements.txt
pip install pyinstaller

echo.
echo ==============================================
echo 4) Downloading Offline Chrome and Driver...
echo ==============================================
echo Downloading 32-bit Chrome for Testing...
python download_chrome.py
if errorlevel 1 (
    echo [ERROR] Failed to download Chrome!
    pause
    exit /b 1
)

echo.
echo ==============================================
echo 5) Building RPA Agent Executable...
echo ==============================================
echo Cleaning old build...
if exist "dist" rmdir /S /Q "dist"
if exist "build" rmdir /S /Q "build"
if exist "rpa_agent_release.zip" del /Q "rpa_agent_release.zip"

echo Compiling rpa_agent.py to standalone executable...
pyinstaller --onefile --noconfirm rpa_agent.py

if exist "dist\rpa_agent.exe" (
    echo.
    echo [SUCCESS] Build complete!

    echo.
    echo ==============================================
    echo 6) Packaging Release Zip...
    echo ==============================================
    echo Copying files to release folder...
    mkdir dist\rpa_agent_release
    copy dist\rpa_agent.exe dist\rpa_agent_release\
    copy start_agent_and_chrome.bat dist\rpa_agent_release\
    xcopy /E /I /Q browser dist\rpa_agent_release\browser

    echo Creating zip archive...
    powershell -Command "Compress-Archive -Path dist\rpa_agent_release\* -DestinationPath rpa_agent_release.zip -Force"

    echo.
    echo [SUCCESS] Package complete!
    echo Your ready-to-deploy zip file is located at: %cd%\rpa_agent_release.zip
    echo.
    echo You can distribute this single zip file to branch users.
) else (
    echo.
    echo [ERROR] Build failed! Check the output above.
)

pause
