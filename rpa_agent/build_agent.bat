@echo off
setlocal enabledelayedexpansion

title Build Local RPA Agent

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

echo.
echo ==============================================
echo 2) Setting up Virtual Environment...
echo ==============================================
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo.
echo ==============================================
echo 3) Installing Dependencies...
echo ==============================================
pip install -r requirements.txt
pip install pyinstaller

echo.
echo ==============================================
echo 4) Building RPA Agent Executable...
echo ==============================================
echo Cleaning old build...
if exist "dist\rpa_agent.exe" del /Q "dist\rpa_agent.exe"
if exist "build" rmdir /S /Q "build"

echo Compiling rpa_agent.py to standalone executable...
pyinstaller --noconfirm rpa_agent.spec

if exist "dist\rpa_agent.exe" (
    echo.
    echo [SUCCESS] Build complete!
    echo Your executable is located at: %cd%\dist\rpa_agent.exe
    echo.
    echo You can distribute this single file along with "start_agent_and_chrome.bat" to branch users.
) else (
    echo.
    echo [ERROR] Build failed! Check the output above.
)

pause
