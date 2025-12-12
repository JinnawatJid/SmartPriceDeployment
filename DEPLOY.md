# Deployment Instructions

This guide explains how to deploy the application on an offline (air-gapped) Windows Server using Docker.

## Prerequisites on the Target Server (Windows Server 2019)

1.  **Docker Desktop** (or Docker Engine) installed and running.
2.  Ensure Docker is switched to **Linux Containers** mode (default for Docker Desktop).

## 1. Prepare Artifacts (On an Online Machine)

1.  Open a terminal in the project root.
2.  Run the build and save script:
    *   **Mac/Linux**: `./save_images.sh`
    *   **Windows**: `.\save_images.ps1`
3.  This will create two files:
    *   `backend.tar`
    *   `frontend.tar`
4.  Copy the following files to a USB drive or secure transfer medium:
    *   `backend.tar`
    *   `frontend.tar`
    *   `docker-compose.offline.yml`
    *   **Required**: `backend/data/Quetung.db` (This is the database file. You must copy it to the server).

## 2. Transfer and Load (On the Offline Server)

1.  Create a folder on the server, e.g., `C:\PricingApp`.
2.  Create a subfolder named `data` inside it: `C:\PricingApp\data`.
3.  **Crucial**: Copy `Quetung.db` into `C:\PricingApp\data`.
    *   *Note: If you skip this, the application will see an empty database and will not function correctly.*
4.  Copy the other files (`backend.tar`, `frontend.tar`, `docker-compose.offline.yml`) into `C:\PricingApp`.
5.  Open PowerShell or Command Prompt as Administrator.
6.  Navigate to the folder:
    ```powershell
    cd C:\PricingApp
    ```
7.  Load the docker images:
    ```powershell
    docker load -i backend.tar
    docker load -i frontend.tar
    ```
    *The images `pricing-backend:latest` and `pricing-frontend:latest` will be restored automatically.*

## 3. Run the Application

1.  Use the offline compose file to start the services:
    ```powershell
    docker-compose -f docker-compose.offline.yml up -d
    ```

## 4. Verify

*   Open a browser on the server (or a connected client) and go to `http://localhost` (or the server IP).
*   The API should be available at `http://localhost/api`.

## Troubleshooting

*   **Ports**: Ensure ports 80 and 4000 are not blocked by the Windows Firewall.
*   **Database**: If the application errors out or shows no data, verify that `C:\PricingApp\data\Quetung.db` exists and is a valid SQLite file.
