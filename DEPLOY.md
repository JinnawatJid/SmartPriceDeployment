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
    *   (Optional) `backend/data/Quetung.db` (Only needed if you want to enable data persistence later).

## 2. Transfer and Load (On the Offline Server)

1.  Create a folder on the server, e.g., `C:\PricingApp`.
2.  Copy the transferred files (`backend.tar`, `frontend.tar`, `docker-compose.offline.yml`) into `C:\PricingApp`.
3.  Open PowerShell or Command Prompt as Administrator.
4.  Navigate to the folder:
    ```powershell
    cd C:\PricingApp
    ```
5.  Load the docker images:
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

## Advanced: Enabling Data Persistence

By default, the application runs with an embedded database. Any changes (new customers, quotes) will be **lost** if the container is removed.

To enable persistence:

1.  Stop the containers:
    ```powershell
    docker-compose -f docker-compose.offline.yml down
    ```
2.  Create a folder named `data` inside `C:\PricingApp`.
3.  **Crucial**: Copy your `Quetung.db` file into `C:\PricingApp\data`.
4.  Edit `docker-compose.offline.yml` using Notepad:
    *   Uncomment the `volumes:` section.
    *   It should look like this:
        ```yaml
        volumes:
          - ./data:/app/data
        ```
5.  Start the containers again:
    ```powershell
    docker-compose -f docker-compose.offline.yml up -d
    ```

## Troubleshooting

*   **Ports**: Ensure ports 80 and 4000 are not blocked by the Windows Firewall.
*   **Database Error**: If you see "No such table", it means you enabled persistence (volumes) but failed to copy the `Quetung.db` file into the `data` folder correctly.
