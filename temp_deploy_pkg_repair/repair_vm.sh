#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "=== 1. System Prep ==="
sudo apt-get update
sudo apt-get install -y curl unzip

echo "=== 2. Docker Check ==="
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed."
else
    echo "Docker already installed."
fi

echo "=== 3. Redeploying ==="
# Cleanup potential locks from failed installs
sudo rm -rf /var/lib/apt/lists/lock
sudo rm -rf /var/cache/apt/archives/lock || true

# Prepare directory
rm -rf synapse-deploy
mkdir synapse-deploy
unzip -o ~/source.zip -d synapse-deploy
cd synapse-deploy

echo "Stopping existing containers..."
sudo docker compose -f docker-compose.prod.yml down --remove-orphans || true

echo "Starting containers..."
sudo docker compose -f docker-compose.prod.yml up -d --build

echo "=== Repair Complete ==="
