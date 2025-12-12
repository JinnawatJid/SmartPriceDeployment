# PowerShell script to save Docker images

$backendImage = "pricing-backend:latest"
$frontendImage = "pricing-frontend:latest"

Write-Host "Building images..."
docker-compose build

Write-Host "Saving Backend Image ($backendImage)..."
docker save -o backend.tar $backendImage

Write-Host "Saving Frontend Image ($frontendImage)..."
docker save -o frontend.tar $frontendImage

Write-Host "Images saved to backend.tar and frontend.tar"
