# Smart Pricing System - Native Windows Deployment

This document provides instructions on how to build and deploy the Smart Pricing System as a native Windows application bundle. This approach avoids Docker and runs the application directly as a self-contained executable.

## Prerequisites

### For Building (Developer Machine)
- Windows 10/11
- Python 3.10+ (Ensure `pip` is in PATH)
- Node.js 18+ (Ensure `npm` is in PATH)

### For Hosting (Target Server)
- Windows Server 2019 (or Windows 10/11)
- **GTK3 Runtime**: Required for PDF generation (`WeasyPrint`).

---

## 1. Building the Release

1.  Open **Command Prompt (cmd)** or PowerShell on your developer machine.
2.  Navigate to the root directory of this project.
3.  Run the build script:
    ```cmd
    create_release.bat
    ```
4.  This script will:
    -   Install Python dependencies.
    -   Install Node.js dependencies and build the React frontend.
    -   Package the backend and frontend into a single executable using PyInstaller.
    -   Create a `Release` folder containing the ready-to-deploy application.

---

## 2. Preparing the Offline Bundle

To facilitate offline deployment:

1.  Download the **GTK3 Runtime Installer** (e.g., `gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe`) from [GitHub - tschoonj/GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
2.  Place the `.exe` file **inside the `Release` folder** you just created (next to `start_server.bat`).
    -   *Why?* The `start_server.bat` script is designed to look for this file and install it automatically if the server is missing the required DLLs.

Your `Release` folder should look like this:
```text
Release/
├── data/                  <-- Database folder (Quetung.db)
├── smart_pricing/         <-- Application Binaries
├── start_server.bat       <-- Launch Script
└── gtk3-runtime-x.x.x.exe <-- Installer you just downloaded
```

3.  Zip the `Release` folder and transfer it to your air-gapped server.

---

## 3. Running on the Server

1.  Unzip the deployment on the target server.
2.  Double-click **`start_server.bat`**.
3.  **First Run Check**:
    -   The script will check if GTK3 is installed.
    -   If missing, it will launch the installer you included. Follow the prompts to install it.
    -   If already installed, it proceeds immediately.
4.  The application will start, and a browser window will open at:
    `http://localhost:3200`

---

## 4. Updates & Data Persistence

- The database is stored in the `Release/data/` folder.
- **To Update the App**:
    1.  Stop the running server (close the console window).
    2.  Replace the `Release/smart_pricing/` folder with the new version.
    3.  **Do NOT delete the `Release/data/` folder**, or you will lose your data.
