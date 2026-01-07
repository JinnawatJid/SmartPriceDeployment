# Smart Pricing - Offline Deployment Instructions

This guide explains how to deploy the application on an **offline (air-gapped) Windows Server**.
You can choose between the **Docker Method** (Recommended) or the **Native Fallback Method**.

---

## 🚀 Option 1: Docker Deployment (Recommended)

This method runs the application in isolated containers (Nginx + Python), ensuring consistency.

### Phase 1: Preparation (On an Online Machine)
1. Ensure Docker Desktop is installed and running.
2. Open PowerShell in the project root.
3. Run the image export script:
   ```powershell
   .\save_images.ps1
   ```
   *This will build the images and create two files: `backend.tar` and `frontend.tar`.*

### Phase 2: Transfer
Copy the following files to your USB drive or transfer them to the offline server:
- `backend.tar`
- `frontend.tar`
- `docker-compose.yml`

### Phase 3: Installation (On the Offline Server)
1. Ensure Docker Desktop is installed on the server.
2. Open PowerShell in the folder where you copied the files.
3. Load the images:
   ```powershell
   docker load -i backend.tar
   docker load -i frontend.tar
   ```
4. Start the application:
   ```powershell
   docker-compose up -d
   ```
5. Access the application at: **http://localhost:3200**
   *(Note: The Frontend listens on port 3200, which talks to the Backend on port 8000 internally.)*

---

## 💻 Option 2: Native Windows Deployment (Fallback)

This method runs the application as a standalone `.exe` file directly on Windows.

### Phase 1: Preparation (On an Online Machine)
1. Ensure Python 3.9+ and Node.js are installed.
2. Open Command Prompt (cmd) in the project root.
3. Run the release builder:
   ```cmd
   create_release.bat
   ```
   *This will compile everything and create a release folder at `dist\smart_pricing\`.*

### Phase 2: Transfer
Copy the entire `dist\smart_pricing\` folder to the offline server.

### Phase 3: Installation (On the Offline Server)
1. **Install GTK3 Runtime (Required for PDF Generation):**
   - Download and install the **GTK3 Runtime for Windows** (64-bit recommended).
   - *If you don't have the installer, download it on the online machine from [here](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer) and transfer it.*
2. Open the `smart_pricing` folder you copied.
3. Run the server launcher:
   ```cmd
   start_server.bat
   ```
4. Access the application at: **http://localhost:8000**
   *(Note: In Native mode, the backend directly serves the frontend on port 8000.)*

---

## ❓ Troubleshooting

- **PDF Generation Fails (Native):** Ensure GTK3 Runtime is installed and `libcairo-2.dll` is in the path.
- **Port In Use:**
  - Docker: Edit `docker-compose.yml` and change `"3200:80"` to `"YOUR_PORT:80"`.
  - Native: The port 8000 is default.
- **Database:**
  - **Docker:** Data is stored inside the container (as per request). Resetting the container resets data.
  - **Native:** Data is stored in the `data` folder inside the application folder.
