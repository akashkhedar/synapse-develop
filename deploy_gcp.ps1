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
        --tags="http-server,https-server,synapse-app" `
        --boot-disk-size=30GB
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
Start-Sleep -Seconds 10
$VM_IP = gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
Write-Green "VM Public IP: $VM_IP"

# Create Source Archive using Robocopy for safe exclusion
Write-Green "Creating Source Archive (source.zip)..."
$tempDir = "temp_deploy_msg"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Staging files (excluding node_modules, cache, etc)..."
# Robocopy is robust: /MIR (mirror), /XD (exclude dirs), /XF (exclude files)
$excludeDirs = @("node_modules", ".git", ".idea", ".vscode", "build", "__pycache__", ".venv", ".nx", "site-packages")
$excludeFiles = @("*.pyc", "*.vhdx", "source.zip")
# Removing strict logging flags to avoid parameter errors
robocopy . $tempDir /MIR /XD $excludeDirs /XF $excludeFiles /R:0 /W:0

Write-Host "Zipping staged files..."
Compress-Archive -Path "$tempDir\*" -DestinationPath "source.zip" -Force
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Source archive created."

Write-Green "Deploying to VM..."

Write-Host "Installing Docker on VM (if needed)..."
# Using semicolons to avoid CRLF issues on Linux execution
$installCmd = "export DEBIAN_FRONTEND=noninteractive; sudo apt-get update; if ! command -v docker &> /dev/null; then echo 'Installing Docker...'; curl -fsSL https://get.docker.com -o get-docker.sh; sudo sh get-docker.sh; sudo usermod -aG docker `$USER; fi"
gcloud compute ssh $VM_NAME --zone=$ZONE --command=$installCmd

Write-Host "Uploading source code..."
gcloud compute scp source.zip "${VM_NAME}:." --zone=$ZONE

Write-Host "Building and Starting Application on VM..."
# Using semicolons to avoid CRLF issues
$deployCmd = "export DEBIAN_FRONTEND=noninteractive; sudo apt-get update; sudo apt-get install -y unzip; rm -rf synapse-deploy; mkdir synapse-deploy; unzip -o source.zip -d synapse-deploy; cd synapse-deploy; echo 'Building Docker containers on VM...'; docker compose -f docker-compose.prod.yml up -d --build"
gcloud compute ssh $VM_NAME --zone=$ZONE --command=$deployCmd

# Cleanup local zip
Remove-Item "source.zip" -ErrorAction SilentlyContinue

Write-Green "Deployment Complete!"
Write-Green "Access your app at: http://${VM_IP}:8080"

