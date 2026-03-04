========================================
  RPA CLIENT - STANDALONE PACKAGE
========================================

This package contains everything needed to run RPA on Client machine.
NO Python installation required!

REQUIREMENTS:
- Google Chrome (must be installed)
- Windows 10 or higher

FILES:
- rpa_client/          : RPA executable and dependencies
- start_chrome_debug.bat : Start Chrome with debug mode
- run_rpa.bat          : Run RPA script
- README.txt           : This file

USAGE:

Step 1: Start Chrome
  Double-click: start_chrome_debug.bat
  - Chrome will open with 2 tabs
  - Tab 1: Dynamics 365 BC
  - Tab 2: Smart Pricing System

Step 2: Login to D365 BC
  - Switch to D365 BC tab
  - Login with your credentials
  - Navigate to Sales Quotes page

Step 3: Run RPA
  Double-click: run_rpa.bat
  - Enter Quote Code when prompted (e.g., TRQT)
  - RPA will create Sales Quote automatically

TROUBLESHOOTING:

Chrome not found:
  - Install Chrome from https://www.google.com/chrome/
  - Or update Chrome path in start_chrome_debug.bat

Port 9222 error:
  - Close all Chrome windows
  - Run start_chrome_debug.bat again

RPA fails:
  - Make sure Chrome is running (start_chrome_debug.bat)
  - Make sure you're logged into D365 BC
  - Make sure you're on Sales Quotes page

Connection error:
  - Check that Chrome debug port is open:
    netstat -ano | findstr :9222
  - Should see: TCP 0.0.0.0:9222 ... LISTENING

========================================
  SUPPORT
========================================

For issues or questions, contact IT support.

