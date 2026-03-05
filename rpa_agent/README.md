# Client-Side RPA Agent

The RPA automation for creating Sales Quotes in Dynamics 365 BC has been redesigned from a Server-Side model to a **Client-Side Agent** model (Industry Standard).

## Why the Change?
Previously, the backend server attempted to connect to the client computer's Google Chrome browser over the network via port 9222. This caused numerous issues:
- **Firewall Blocks**: Client computers naturally block inbound traffic on random ports.
- **Dynamic IPs**: The backend had to guess the client's IP address (which changes in branches).
- **Security**: Opening debug ports to the network is a security risk.

## How it Works Now
1. The **Local Agent** (`rpa_agent.exe`) runs on the user's computer alongside Google Chrome.
2. The Agent runs a tiny, local API server on `http://127.0.0.1:8001`.
3. When the user clicks "Send to BC" on the Web App, their browser sends the payload directly to `localhost:8001`.
4. The Local Agent receives the payload and uses Selenium to drive the user's *already open* Chrome browser (`127.0.0.1:9222`) to create the Quote.

---

## 🏗️ Phase 1: Building the Agent (IT Team / Developer)

**⚠️ Requires Internet Access and Python 3.9+**

To distribute the Agent to branch users, you must build it into a standalone `.exe` so they do not need to install Python or connect to the internet to download dependencies (like `pip install`).

1. Ensure Python 3.9+ is installed on your **developer machine**.
2. Open a terminal in the `rpa_agent/` directory.
3. Run `build_agent.bat`.
4. This script will automatically create a virtual environment, download `FastAPI`, `Selenium`, etc. via `pip`, and compile the Python script into a zero-dependency executable using PyInstaller.
5. The final artifact will be located at `rpa_agent/dist/rpa_agent.exe`.

---

## 🚀 Phase 2: Distribution to Branches (Offline)

**✅ No Internet or Python Required on Branch PCs**

Provide the branch users with a ZIP folder containing only these two files:
1. `rpa_agent.exe` (from the `dist` folder generated in Phase 1)
2. `start_agent_and_chrome.bat`

---

## 💻 Daily Usage for Branch Users
1. In the morning, users should run `start_agent_and_chrome.bat`.
2. This script will automatically:
   - Find and launch Google Chrome with the `--remote-debugging-port=9222` flag enabled.
   - Start the `rpa_agent.exe` in the background (a black terminal window will appear).
3. The user must **leave the black terminal window open** while working.
4. They can log into Dynamics 365 BC normally in the Chrome window.
5. **(One-Time Setup)** The user must open a new tab, go to `chrome://flags/#block-insecure-private-network-requests`, and set it to **Disabled**. This allows the internal HTTP web app to communicate with the `localhost` agent.
6. When they create a quote in the web app and click "Send to BC", the Local Agent will take over Chrome and automate the entry.
