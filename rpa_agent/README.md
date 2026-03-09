# Client-Side RPA Agent

The RPA automation for creating Sales Quotes in Dynamics 365 BC operates entirely as a **Client-Side Agent** model. This is an industry-standard approach to Desktop Automation (similar to DBD Bridge Servers) that bypasses network, firewall, and VPN limitations.

## 🏛️ Architecture Concepts

### The Old Way: Server-Side RPA (Why it failed)
Previously, the central API server attempted to initiate a connection to the user's local Google Chrome browser across the internet/VPN (e.g., `192.168.x.x:9222`).
- **Firewall Blocks**: Windows and VPNs (like SonicWall) actively block inbound traffic to random ports like 9222.
- **Dynamic IPs**: The server had to guess the client's IP address, which changes frequently.
- **Port Conflicts**: If the user already had Chrome open, Windows ignored the command to start a new debugging port.

### The New Way: Client-Side Agent
1. The **Local Agent** (`rpa_agent.exe`) runs directly on the user's computer alongside Google Chrome.
2. The Agent runs a tiny API server on `http://127.0.0.1:8001`.
3. When the user clicks "Send to BC" on the Web App, their browser (Frontend) sends the payload directly down to `127.0.0.1:8001` (localhost). The request never travels back over the VPN.
4. The Local Agent receives the payload and uses Selenium to drive the user's local Chrome browser (`127.0.0.1:9222`) to create the Quote.

---

## 🧠 Key Learnings & Problem Resolutions

During development, we encountered three major challenges regarding browser automation that shaped the current architecture:

### 1. The Profile Lock Issue ("Session Not Created: Cannot connect to Chrome at 127.0.0.1:9222")
*   **Problem:** If a user already had Chrome open (or a hidden background process running), running `chrome.exe --remote-debugging-port=9222` would fail silently. Windows simply opened a new tab in the *existing* Chrome process, ignoring the debugging flag entirely, meaning port 9222 never opened.
*   **Solution:** We modified `start_agent_and_chrome.bat` to forcefully launch Chrome using a completely isolated, temporary user profile directory: `--user-data-dir="%TEMP%\chrome_rpa_profile"`. This guarantees Chrome launches a brand-new, independent process that successfully binds to port 9222 every single time, regardless of the user's personal browsing session.

### 2. The PNA CORS Block ("Failed to fetch")
*   **Problem:** Modern browsers enforce "Private Network Access" (PNA) security. They block public internet websites (like the Smart Pricing server) from making API requests to local programs (like the Agent on `127.0.0.1`). Because we started using an isolated `--user-data-dir` (see #1), any manual `chrome://flags` the user had previously set to bypass this were wiped out on every launch.
*   **Solution:** We added the `--disable-features=BlockInsecurePrivateNetworkRequests` flag directly into the `start_agent_and_chrome.bat` script. This automatically bypasses the PNA check for that specific Chrome session, allowing the frontend to talk to the Local Agent without requiring the user to manually configure Chrome flags.

### 3. The Offline Selenium Failure ("Unable to obtain driver for chrome" / HTTP 500)
*   **Problem:** Selenium 4 uses an internal tool called "Selenium Manager" to automatically download the correct `chromedriver.exe` matching the user's installed Chrome version over the internet. Because branch computers operate in strictly offline or restricted network environments, this download failed, causing the RPA agent to crash on startup.
*   **Solution:** We made the agent fully offline-capable. `rpa_agent.py` was updated to check its own directory for a file named `chromedriver.exe`. If found, it explicitly initializes the browser using that local file (`webdriver.Chrome(service=Service(executable_path=...))`), completely bypassing the internet-dependent Selenium Manager.

---

## 🏗️ Phase 1: Building the Agent (IT Team / Developer)

**⚠️ Requires Internet Access and Python 3.9+**

To distribute the Agent to branch users, you must build it into a standalone `.exe` so they do not need to install Python.

1. Ensure Python 3.9+ is installed on your **developer machine**.
   *   *Note: If branch machines are running older 32-bit Windows 10 installations, you MUST install a 32-bit version of Python on your developer machine to compile a compatible 32-bit `.exe`.*
2. Open a terminal in the `rpa_agent/` directory.
3. Run `build_agent.bat`.
4. This script creates a virtual environment, downloads dependencies, and compiles the Python script using PyInstaller.
5. The final artifact will be located at `rpa_agent/dist/rpa_agent.exe`.

---

## 🚀 Phase 2: Distribution to Branches (Offline)

**✅ No Internet or Python Required on Branch PCs**

Provide the branch users with a folder containing exactly these three files:
1. `rpa_agent.exe` (from the `dist` folder generated in Phase 1)
2. `start_agent_and_chrome.bat`
3. `chromedriver.exe` **(CRITICAL)**: You must manually download the exact version of `chromedriver.exe` that matches the branch computer's installed Google Chrome version (e.g., v118) from Google's official ChromeDriver repository and place it in the same folder.

---

## 💻 Daily Usage for Branch Users
1. In the morning, users should double-click `start_agent_and_chrome.bat`.
2. The script will close existing Chrome instances and automatically:
   - Launch Google Chrome with a dedicated RPA profile and remote debugging enabled.
   - Start the `rpa_agent.exe` in the background (a black terminal window will appear).
3. The user must **leave the black terminal window open** while working.
4. They log into Dynamics 365 BC in the newly opened Chrome window.
5. When they create a quote in the web app and click "Send to BC", the Local Agent will take over Chrome and automate the entry.
