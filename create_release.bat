@echo off
setlocal

echo ==================================================
echo      SMART PRICING - RELEASE BUILDER
echo ==================================================

echo 1. Building Frontend...
cd frontend
call npm install
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b %errorlevel%
)
cd ..

echo 2. Installing Backend Requirements...
cd backend
pip install -r requirements.txt
cd ..

echo 3. Running PyInstaller...
pyinstaller --clean smart_pricing.spec

echo ==================================================
echo      BUILD COMPLETE
echo ==================================================
echo The executable is located in 'dist/smart_pricing/'
pause
