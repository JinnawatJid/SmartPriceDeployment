#!/bin/bash

# Define image names
BACKEND_IMAGE="pricing-backend:latest"
FRONTEND_IMAGE="pricing-frontend:latest"

# Build the images first
echo "Building images..."
docker-compose build

echo "Saving Backend Image ($BACKEND_IMAGE)..."
docker save -o backend.tar $BACKEND_IMAGE

echo "Saving Frontend Image ($FRONTEND_IMAGE)..."
docker save -o frontend.tar $FRONTEND_IMAGE

echo "Images saved to backend.tar and frontend.tar"
echo "Transfer these files to your offline server."
