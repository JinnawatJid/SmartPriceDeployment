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
echo 1) Select Target Architecture...
echo ==============================================
echo The branch machines require a 32-bit executable.
echo Your system default Python might be 64-bit.
echo.
echo Please select the architecture you want to build for:
echo [1] 32-bit (For Branch Machines - Recommended)
echo [2] 64-bit (For Local Testing Only)
echo.
set /p ARCH_CHOICE="Enter 1 or 2: "

if "%ARCH_CHOICE%"=="1" (
    set TARGET_ARCH=32
    echo You selected: 32-bit Build
) else if "%ARCH_CHOICE%"=="2" (
    set TARGET_ARCH=64
    echo You selected: 64-bit Build
) else (
    echo Invalid choice. Exiting.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo 2) Locating Python Installation...
echo ==============================================

set "PYTHON_EXE="

if "%TARGET_ARCH%"=="32" (
    echo Searching for 32-bit Python...

    :: Attempt 1: Try the Python Launcher 'py' targeting 32-bit
    py -3-32 -c "import platform,sys; sys.exit(0) if platform.architecture()[0]=='32bit' else sys.exit(1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py -3-32"
        goto :FOUND_PYTHON
    )

    :: Attempt 2: Check common installation paths for 32-bit Python
    for %%P in (
        "C:\Python312-32\python.exe"
        "C:\Python311-32\python.exe"
        "%LocalAppData%\Programs\Python\Python312-32\python.exe"
        "%LocalAppData%\Programs\Python\Python311-32\python.exe"
        "C:\Program Files (x86)\Python312-32\python.exe"
    ) do (
        if exist "%%~P" (
            "%%~P" -c "import platform,sys; sys.exit(0) if platform.architecture()[0]=='32bit' else sys.exit(1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_EXE="%%~P""
                goto :FOUND_PYTHON
            )
        )
    )

    :: Attempt 3: Check if default python is 32-bit
    python -c "import platform,sys; sys.exit(0) if platform.architecture()[0]=='32bit' else sys.exit(1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        goto :FOUND_PYTHON
    )

    echo [ERROR] Could not find a 32-bit Python installation!
    echo Please download and install the "Windows installer (32-bit)" for Python 3.12 or 3.11.
    pause
    exit /b 1
) else (
    echo Searching for 64-bit Python...

    :: Attempt 1: Check default python
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        goto :FOUND_PYTHON
    )

    :: Attempt 2: Try Python Launcher
    py -3 -V >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py -3"
        goto :FOUND_PYTHON
    )

    echo [ERROR] Could not find any Python installation!
    pause
    exit /b 1
)

:FOUND_PYTHON
echo [OK] Using Python interpreter: %PYTHON_EXE%
%PYTHON_EXE% -V
%PYTHON_EXE% -c "import platform; print('Architecture:', platform.architecture()[0])"

echo.
echo ==============================================
echo 3) Setting up Virtual Environment...
echo ==============================================
echo Removing corrupted or old virtual environment (if any)...
if exist "venv" rmdir /S /Q "venv"

echo Creating fresh virtual environment...
%PYTHON_EXE% -m venv venv
call venv\Scripts\activate.bat

echo.
echo ==============================================
echo 3) Installing Dependencies...
echo ==============================================
echo Using verbose output to show build progress (compiling packages may take several minutes)...
pip install -v -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    echo Please check the error logs above.
    pause
    exit /b 1
)

pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller!
    pause
    exit /b 1
)

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

if not exist "dist\rpa_agent.exe" goto BUILD_FAILED

echo.
echo [SUCCESS] Build complete!

echo.
echo ==============================================
echo 6) Packaging Release Zip...
echo ==============================================
echo Copying files to release folder...
mkdir "dist\rpa_agent_release"
copy "dist\rpa_agent.exe" "dist\rpa_agent_release\"
copy "start_agent_and_chrome.bat" "dist\rpa_agent_release\"
xcopy /E /I /Q "browser" "dist\rpa_agent_release\browser"

echo Creating zip archive...
powershell -Command "Compress-Archive -Path dist\rpa_agent_release\* -DestinationPath rpa_agent_release.zip -Force"

echo.
echo [SUCCESS] Package complete!
echo Your ready-to-deploy zip file is located at: "%cd%\rpa_agent_release.zip"
echo.
echo You can distribute this single zip file to branch users.
pause
exit /b 0

:BUILD_FAILED
echo.
echo [ERROR] Build failed! Check the output above.
pause
exit /b 1
