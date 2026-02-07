# deploy_gcp.ps1 - Windows Deployment Script for Synapse to GCP
# Usage: .\deploy_gcp.ps1 [-ProjectId "your-project-id"]

param (
    [string]$ProjectId = "synapse-485809"
)

$ErrorActionPreference = "Stop"

# ==========================================
# Helper Functions
# ==========================================
function Write-Green($text) { Write-Host $text -ForegroundColor Green }
function Write-Yellow($text) { Write-Host $text -ForegroundColor Yellow }
function Write-Red($text) { Write-Host $text -ForegroundColor Red }

# ==========================================
# Pre-flight Checks
# ==========================================
Write-Green "Starting Deployment Verification..."

if (-not (Get-Command "gcloud" -ErrorAction SilentlyContinue)) {
    Write-Red "Error: Google Cloud SDK (gcloud) is not installed."
    exit 1
}

# Verify Project ID
$currentProject = gcloud config get-value project 2>$null
if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    if ([string]::IsNullOrWhiteSpace($currentProject)) {
        Write-Red "Error: No GCP Project ID provided and none set in gcloud config."
        exit 1
    }
    $ProjectId = $currentProject
}
Write-Green "Target GCP Project: $ProjectId"
gcloud config set project $ProjectId

# Enable Services
Write-Green "Enabling required GCP services..."
gcloud services enable compute.googleapis.com

# ==========================================
# VM Infrastructure
# ==========================================
$VM_NAME = "synapse-monolith"
$ZONE = "asia-south1-a"
$MACHINE_TYPE = "e2-medium"

Write-Green "Checking for existing VM ($VM_NAME)..."
$vmCheck = gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(status)" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Yellow "VM not found. Creating new VM..."
    gcloud compute instances create $VM_NAME `
        --zone=$ZONE `
        --machine-type=$MACHINE_TYPE `
        --image-family=ubuntu-2204-lts `
        --image-project=ubuntu-os-cloud `
        --tags="http-server,https-server,synapse-app" `
        --boot-disk-size=40GB `
        --boot-disk-type=pd-ssd
} else {
    Write-Green "VM exists."
    if ($vmCheck -ne "RUNNING") {
        Write-Yellow "Starting VM..."
        gcloud compute instances start $VM_NAME --zone=$ZONE
    }
}

# Firewall Rules
Write-Green "Configuring Firewall..."
$fwCheck = gcloud compute firewall-rules describe allow-synapse-ports --format="value(name)" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud compute firewall-rules create allow-synapse-ports `
        --allow="tcp:8080,tcp:9000,tcp:9001" `
        --target-tags=synapse-app `
        --description="Allow Synapse Application Ports"
}

# Get VM IP
Write-Yellow "Waiting for VM Public IP..."
Start-Sleep -Seconds 5
$VM_IP = gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
if ([string]::IsNullOrWhiteSpace($VM_IP)) {
    Write-Red "Error: Could not retrieve VM IP address."
    exit 1
}
Write-Green "VM IP Address: $VM_IP"

# ==========================================
# Configuration Generation
# ==========================================
Write-Green "Generating production environment configuration..."

if (-not (Test-Path ".env")) {
    Write-Red "Error: .env file not found. Please create one from .env.example"
    exit 1
}

$envContent = Get-Content ".env"
$prodEnvContent = @()

foreach ($line in $envContent) {
    if ($line -match "^DEBUG=") { $line = "DEBUG=False" }
    # Database uses internal docker service name
    if ($line -match "^POSTGRE_HOST=") { $line = "POSTGRE_HOST=db" }
    if ($line -match "^REDIS_HOST=") { $line = "REDIS_HOST=redis" }
    # Storage needs public access point
    if ($line -match "^STORAGE_AWS_ENDPOINT_URL=") { $line = "STORAGE_AWS_ENDPOINT_URL=http://$($VM_IP):9000" }
    # Allowed hosts
    if ($line -match "^ALLOWED_HOSTS=") { $line = "ALLOWED_HOSTS=localhost,127.0.0.1,$VM_IP" }
    if ($line -match "^CORS_ALLOWED_ORIGINS=") { $line = "CORS_ALLOWED_ORIGINS=http://localhost:8080,http://$($VM_IP):8080,http://$($VM_IP):9000" }
    
    $prodEnvContent += $line
}

$prodEnvContent | Set-Content "production.env"
Write-Green "production.env created."

# ==========================================
# Packaging & Deployment
# ==========================================
Write-Green "Packaging application..."
$tempDir = "temp_deploy_pkg"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Robocopy allow list equivalent (simpler with copy)
$items = @("synapse", "synapse-sdk", "web", "Dockerfile", "docker-compose.prod.yml", "production.env", "pyproject.toml", "poetry.lock")
foreach ($item in $items) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination "$tempDir\$item" -Recurse -Force
    }
}

# Zip it
if (Test-Path "source.zip") { Remove-Item "source.zip" -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath "source.zip" -Force
Remove-Item $tempDir -Recurse -Force

Write-Green "Uploading to VM..."
# Using scp with strict host checking disabled to avoid prompts
gcloud compute scp source.zip "${VM_NAME}:~/source.zip" --zone=$ZONE 

Write-Green "Executing Remote Deployment..."
$deployScript = @"
set -e
export DEBIAN_FRONTEND=noninteractive

# Install Docker if missing
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker `$USER
fi

# Clean previous
rm -rf deploy_app
mkdir deploy_app
unzip -o ~/source.zip -d deploy_app
cd deploy_app

# Deploy
echo "Starting Docker Compose..."
# Stop existing containers to ensure rebuild
sudo docker compose -f docker-compose.prod.yml down --remove-orphans
sudo docker compose -f docker-compose.prod.yml up -d --build

echo "Deployment finished successfully."
"@

gcloud compute ssh $VM_NAME --zone=$ZONE --command=$deployScript

# Cleanup
Remove-Item "source.zip" -Force
Remove-Item "production.env" -Force

Write-Green "=========================================="
Write-Green "Deployment Complete!"
Write-Green "App URL: http://$($VM_IP):8080"
Write-Green "MinIO URL: http://$($VM_IP):9001 (Console)"
Write-Green "=========================================="


