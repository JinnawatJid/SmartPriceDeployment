@echo off
echo ==================================================
echo   BUILD RPA CLIENT EXECUTABLE
echo ==================================================
echo.
echo This will create a standalone RPA executable for Client
echo No Python installation required on Client machine!
echo.
pause

echo.
echo 1. Installing PyInstaller (if needed)...
pip install pyinstaller

echo.
echo 2. Building RPA Client executable...
pyinstaller rpa_client.spec --clean

echo.
echo 3. Creating deployment package...
if not exist "RPA_Client_Deploy" mkdir RPA_Client_Deploy

echo Copying executable...
xcopy /E /I /Y dist\rpa_client RPA_Client_Deploy\rpa_client

echo.
echo 4. Creating start_chrome_debug.bat...
(
echo @echo off
echo echo ==================================================
echo echo   START CHROME WITH DEBUG MODE
echo echo ==================================================
echo echo.
echo echo Starting Chrome with remote debugging...
echo echo Chrome will listen on 0.0.0.0:9222
echo echo.
echo.
echo REM Close existing Chrome instances
echo taskkill /F /IM chrome.exe 2^^^>nul
echo timeout /t 2 /nobreak ^^^>nul
echo.
echo REM Start Chrome with debug mode
echo start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^^
echo   --remote-debugging-port=9222 ^^
echo   --remote-debugging-address=0.0.0.0 ^^
echo   --remote-allow-origins=* ^^
echo   --user-data-dir="%%TEMP%%\chrome-debug-profile" ^^
echo   "http://192.192.0.36:8080/BCTNG" ^^
echo   "http://192.192.0.37:8000/"
echo.
echo echo.
echo echo Chrome started!
echo echo Tab 1: Dynamics 365 BC
echo echo Tab 2: Smart Pricing System
echo echo.
echo echo You can now run rpa_client.exe
echo echo.
echo pause
) > RPA_Client_Deploy\start_chrome_debug.bat

echo.
echo 5. Creating run_rpa.bat...
(
echo @echo off
echo echo ==================================================
echo echo   RUN RPA CLIENT
echo echo ==================================================
echo echo.
echo.
echo REM Check if Chrome is running
echo tasklist /FI "IMAGENAME eq chrome.exe" 2^^^>NUL ^| find /I /N "chrome.exe"^^^>NUL
echo if "%%ERRORLEVEL%%"=="1" ^(
echo     echo [ERROR] Chrome is not running!
echo     echo Please run start_chrome_debug.bat first
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check if port 9222 is open
echo netstat -ano ^| findstr :9222 ^^^>nul
echo if "%%ERRORLEVEL%%"=="1" ^(
echo     echo [ERROR] Chrome debug port 9222 is not open!
echo     echo Please run start_chrome_debug.bat first
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [OK] Chrome is running with debug mode
echo echo.
echo.
echo REM Get quote code from user
echo set /p QUOTE_CODE="Enter Quote Code (e.g., TRQT): "
echo if "%%QUOTE_CODE%%"=="" ^(
echo     echo [ERROR] Quote code is required
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo.
echo echo Running RPA for quote: %%QUOTE_CODE%%
echo echo.
echo.
echo cd rpa_client
echo rpa_client.exe %%QUOTE_CODE%%
echo cd ..
echo.
echo echo.
echo echo ==================================================
echo echo   RPA COMPLETE
echo echo ==================================================
echo echo.
echo pause
) > RPA_Client_Deploy\run_rpa.bat

echo.
echo 6. Creating README.txt...
(
echo ========================================
echo   RPA CLIENT - STANDALONE PACKAGE
echo ========================================
echo.
echo This package contains everything needed to run RPA on Client machine.
echo NO Python installation required!
echo.
echo REQUIREMENTS:
echo - Google Chrome (must be installed^)
echo - Windows 10 or higher
echo.
echo FILES:
echo - rpa_client/          : RPA executable and dependencies
echo - start_chrome_debug.bat : Start Chrome with debug mode
echo - run_rpa.bat          : Run RPA script
echo - README.txt           : This file
echo.
echo USAGE:
echo.
echo Step 1: Start Chrome
echo   Double-click: start_chrome_debug.bat
echo   - Chrome will open with 2 tabs
echo   - Tab 1: Dynamics 365 BC
echo   - Tab 2: Smart Pricing System
echo.
echo Step 2: Login to D365 BC
echo   - Switch to D365 BC tab
echo   - Login with your credentials
echo   - Navigate to Sales Quotes page
echo.
echo Step 3: Run RPA
echo   Double-click: run_rpa.bat
echo   - Enter Quote Code when prompted (e.g., TRQT^)
echo   - RPA will create Sales Quote automatically
echo.
echo TROUBLESHOOTING:
echo.
echo Chrome not found:
echo   - Install Chrome from https://www.google.com/chrome/
echo   - Or update Chrome path in start_chrome_debug.bat
echo.
echo Port 9222 error:
echo   - Close all Chrome windows
echo   - Run start_chrome_debug.bat again
echo.
echo RPA fails:
echo   - Make sure Chrome is running (start_chrome_debug.bat^)
echo   - Make sure you're logged into D365 BC
echo   - Make sure you're on Sales Quotes page
echo.
echo Connection error:
echo   - Check that Chrome debug port is open:
echo     netstat -ano ^| findstr :9222
echo   - Should see: TCP 0.0.0.0:9222 ... LISTENING
echo.
echo ========================================
echo   SUPPORT
echo ========================================
echo.
echo For issues or questions, contact IT support.
echo.
) > RPA_Client_Deploy\README.txt

echo.
echo 7. Creating ZIP package...
powershell -Command "Compress-Archive -Path RPA_Client_Deploy\* -DestinationPath RPA_Client_Deploy.zip -Force"

echo.
echo ==================================================
echo   BUILD COMPLETE!
echo ==================================================
echo.
echo Deployment package created:
echo   Folder: RPA_Client_Deploy\
echo   ZIP:    RPA_Client_Deploy.zip
echo.
echo To deploy:
echo 1. Copy RPA_Client_Deploy.zip to Client machine
echo 2. Extract the ZIP file
echo 3. Run start_chrome_debug.bat
echo 4. Run run_rpa.bat
echo.
echo No Python installation needed on Client!
echo.
pause
