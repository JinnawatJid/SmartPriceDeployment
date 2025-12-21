@echo off
REM create_release.bat
REM Run this script on a Windows machine with Python and Node.js installed to build the release.

echo ==========================================
echo 1. Installing Backend Dependencies...
echo ==========================================
pip install -r backend/requirements.txt
if %errorlevel% neq 0 goto :error

echo ==========================================
echo 2. Installing Frontend Dependencies ^& Building...
echo ==========================================
cd frontend
call npm install
if %errorlevel% neq 0 (
    cd ..
    goto :error
)
call npm run build
if %errorlevel% neq 0 (
    cd ..
    goto :error
)
cd ..

echo ==========================================
echo 3. Building Executable with PyInstaller...
echo ==========================================
pyinstaller smart_pricing.spec --clean --noconfirm
if %errorlevel% neq 0 goto :error

echo ==========================================
echo 4. Packaging Release...
echo ==========================================
if exist Release rmdir /s /q Release
mkdir Release

REM Copy the bundled application
xcopy /E /I dist\smart_pricing Release\smart_pricing
if %errorlevel% neq 0 goto :error

REM Copy the startup script
copy start_server.bat Release\
if %errorlevel% neq 0 goto :error

REM Copy the initial database to the release folder structure
REM Structure:
REM Release/
REM   start_server.bat
REM   smart_pricing/ (the exe folder)
REM   data/ (the persistent data folder)
mkdir Release\data
copy backend\data\Quetung.db Release\data\
if %errorlevel% neq 0 goto :error

echo ==========================================
echo Release created in "Release" folder.
echo You can zip this folder and send it to the server.
echo ==========================================
pause
exit /b 0

:error
echo.
echo ==========================================
echo ERROR: An error occurred during the process.
echo Please check the error messages above.
echo ==========================================
pause
exit /b 1
