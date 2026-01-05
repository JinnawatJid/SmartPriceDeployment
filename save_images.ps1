# save_images.ps1
# Script to save Docker images for offline deployment

$ErrorActionPreference = "Stop"

Write-Host "Building images..."
docker-compose build

Write-Host "Saving Backend Image..."
docker save -o backend.tar smart_pricing_backend

Write-Host "Saving Frontend Image..."
docker save -o frontend.tar smart_pricing_frontend

Write-Host "Done! Transfer 'backend.tar' and 'frontend.tar' to the offline machine."
Write-Host "On the offline machine, run 'docker load -i backend.tar' and 'docker load -i frontend.tar'."
