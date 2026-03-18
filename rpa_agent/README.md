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
*   **Problem:** Selenium 4 uses an internal tool called "Selenium Manager" to automatically download the correct `chromedriver.exe` matching the user's installed Chrome version over the internet. Because branch computers operate in strictly offline or restricted network environments, this download failed, causing the RPA agent to crash on startup. Furthermore, matching the ChromeDriver to the host machine's auto-updating Chrome browser was a constant maintenance nightmare for the IT team.
*   **Solution:** We adopted an industry-standard offline bundling approach. The build script now automatically downloads a portable **32-bit Chrome for Testing** and its matching **ChromeDriver**. These are bundled into a `browser` directory. The `start_agent_and_chrome.bat` script launches this specific bundled browser instead of the system Chrome. This completely isolates the RPA agent from host OS browser updates and internet dependency.

### 4. The 32-bit Architecture Compatibility & Heavy Dependencies
*   **Problem:** Branch machines run 32-bit Windows, meaning a 64-bit `.exe` would instantly crash with a "not compatible" error. Additionally, building the `.exe` with `fastapi` and `pydantic` occasionally failed because some dependencies required a Rust C++ compiler.
*   **Solution:** `build_agent.bat` was updated with an interactive menu that automatically locates a 32-bit Python installation on the developer's machine (without messing up their global 64-bit PATH) to guarantee a 32-bit build. Furthermore, `fastapi` was stripped out entirely; the agent now uses Python's ultra-lightweight, built-in `http.server`, removing the need for a Rust compiler and resulting in a much faster, cleaner build process.

---

## 🏗️ Phase 1: Building the Agent (IT Team / Developer)

**⚠️ Requires Internet Access**

To distribute the Agent to branch users, you must build it into a self-contained release package.

1. Ensure a **32-bit version of Python** is installed on your developer machine (download the "Windows installer (32-bit)" from python.org). You do **not** need to add it to your PATH if you already have a 64-bit version installed.
2. Open a terminal in the `rpa_agent/` directory.
3. Run `build_agent.bat`.
4. The script will present an interactive menu. **Select Option [1] for 32-bit build.**
5. The script will automatically locate your 32-bit Python, download the portable Chrome browser, compile the script using PyInstaller, and package everything together.
6. The final artifact will be a single zip file located at `rpa_agent/rpa_agent_release.zip`.

---

## 🚀 Phase 2: Distribution to Branches (Offline)

**✅ No Internet or Python Required on Branch PCs**

Deploying to the branch is now incredibly simple:
1. Send `rpa_agent_release.zip` to the branch machine.
2. Have the branch user (or IT) extract the zip file to their Desktop or C: drive.
3. Inside the extracted folder, they will find everything pre-configured (`rpa_agent.exe`, the `browser/` folder, and the launcher script).

---

## 💻 Daily Usage for Branch Users
1. In the morning, users should double-click `start_agent_and_chrome.bat`.
2. The script will close existing Chrome instances and automatically:
   - Launch Google Chrome with a dedicated RPA profile and remote debugging enabled.
   - Start the `rpa_agent.exe` in the background (a black terminal window will appear).
3. The user must **leave the black terminal window open** while working.
4. They log into Dynamics 365 BC in the newly opened Chrome window.
5. When they create a quote in the web app and click "Send to BC", the Local Agent will take over Chrome and automate the entry.
