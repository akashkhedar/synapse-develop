# deploy_gcp.ps1 - Windows Deployment Script for Synapse to GCP

$ErrorActionPreference = "Stop"

# ==========================================
# Configuration - Edit these values
# ==========================================
$PROJECT_ID="synapse-485809"
$REGION="asia-south1"
$APP_NAME = "synapse-platform"
$REPO_NAME = "synapse-repo"
$DB_INSTANCE_NAME = "synapse-db"
$REDIS_INSTANCE_NAME = "synapse-redis"

# Colors (simulated for PowerShell)
function Write-Green($text) {
    Write-Host $text -ForegroundColor Green
}
function Write-Yellow($text) {
    Write-Host $text -ForegroundColor Yellow
}

Write-Green "Starting Deployment for $APP_NAME..."

# Check dependencies
if (-not (Get-Command "gcloud" -ErrorAction SilentlyContinue)) {
    Write-Error "gcloud command not found. Please install Google Cloud SDK."
    exit 1
}

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "docker command not found. Please install Docker."
    exit 1
}

# Set Project
Write-Green "Setting GCP Project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable APIs
Write-Green "Enabling required GCP APIs..."
# Added vpcaccess for networking if needed, though we try direct VPC first
gcloud services enable `
    artifactregistry.googleapis.com `
    run.googleapis.com `
    sqladmin.googleapis.com `
    redis.googleapis.com `
    compute.googleapis.com `
    servicenetworking.googleapis.com `
    vpcaccess.googleapis.com

# Create Artifact Registry Repo
Write-Green "Creating/Verifying Artifact Registry Repository..."
$repoCheck = gcloud artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID 2>&1
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create $REPO_NAME `
        --repository-format=docker `
        --location=$REGION `
        --description="Docker repository for Synapse Platform"
    Write-Host "Repository created."
} else {
    Write-Host "Repository exists."
}

# Build Docker Image
$IMAGE_URI = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest"
Write-Green "Building Docker Image..."
docker build --platform linux/amd64 -t $IMAGE_URI .
if ($LASTEXITCODE -ne 0) { Write-Error "Docker build failed"; exit 1 }

# Push Docker Image
Write-Green "Pushing Docker Image to Registry..."
docker push $IMAGE_URI
if ($LASTEXITCODE -ne 0) { Write-Error "Docker push failed"; exit 1 }

$VM_NAME = "synapse-vm"
$ZONE = "${REGION}-a"

# Create/Check VM
Write-Green "Checking Compute Engine VM..."
$vmCheck = gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating VM ($VM_NAME) - e2-medium (Ubuntu)..."
    gcloud compute instances create $VM_NAME `
        --zone=$ZONE `
        --machine-type=e2-medium `
        --image-family=ubuntu-2204-lts `
        --image-project=ubuntu-os-cloud `
        --tags=http-server,https-server,synapse-app `
        --boot-disk-size=20GB
} else {
    Write-Host "VM exists."
}

# Firewall Rules
Write-Green "Ensuring Firewall Rules..."
$fwCheck = gcloud compute firewall-rules describe allow-synapse-8080 --project=$PROJECT_ID 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating firewall rule for port 8080..."
    gcloud compute firewall-rules create allow-synapse-8080 `
        --allow=tcp:8080 `
        --target-tags=synapse-app `
        --description="Allow Synapse Traffic"
}

# Wait for VM to be ready
Write-Host "Waiting for VM to be ready..."
Start-Sleep -Seconds 20

# Get VM IP
$VM_IP = gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
Write-Green "VM Public IP: $VM_IP"

# Create env file locally if needed (already done by user, hopefully)
if (-not (Test-Path "production.env")) {
    Write-Error "production.env NOT FOUND! Please create it first."
    exit 1
}

# Update IMAGE_URI in docker-compose.prod.yml dynamically?
# Better: export IMAGE_URI in the VM env.

Write-Green "Deploying headers to VM..."
# We use gcloud compute ssh/scp
# Protocol: 
# 1. Install Docker (if not exists)
# 2. Copy files
# 3. Run compose

Write-Host "Installing Docker on VM (if needed)..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    if ! command -v docker &> /dev/null; then
        echo 'Installing Docker...'
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker `$USER
    fi
"

Write-Host "Copying configuration files..."
gcloud compute scp production.env docker-compose.prod.yml "${VM_NAME}:~/" --zone=$ZONE

Write-Host "Starting Application on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    export IMAGE_URI='${IMAGE_URI}'
    docker compose -f docker-compose.prod.yml up -d
"

Write-Green "Deployment Complete!"
Write-Green "Access your app at: http://${VM_IP}:8080"

