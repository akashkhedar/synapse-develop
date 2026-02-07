# repair_deploy.ps1
$ErrorActionPreference = "Stop"

$VM_NAME = "synapse-monolith"
$ZONE = "asia-south1-a"

# 1. Get VM IP & Generate Config (Essential for valid source.zip)
Write-Host "Fetching VM IP..." -ForegroundColor Yellow
$VM_IP = gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
if ([string]::IsNullOrWhiteSpace($VM_IP)) { Write-Error "Could not get VM IP"; exit 1 }
Write-Host "VM IP: $VM_IP"

Write-Host "Generating production.env..." -ForegroundColor Yellow
$envContent = Get-Content ".env"
$prodEnvContent = @()
foreach ($line in $envContent) {
    if ($line -match "^DEBUG=") { $line = "DEBUG=False" }
    if ($line -match "^POSTGRE_HOST=") { $line = "POSTGRE_HOST=db" }
    if ($line -match "^REDIS_HOST=") { $line = "REDIS_HOST=redis" }
    # Map Django env vars to Docker Postgres vars
    if ($line -match "^POSTGRE_USER=(.*)") { $prodEnvContent += "POSTGRES_USER=$($matches[1])" }
    if ($line -match "^POSTGRE_PASSWORD=(.*)") { $prodEnvContent += "POSTGRES_PASSWORD=$($matches[1])" }
    if ($line -match "^POSTGRE_NAME=(.*)") { $prodEnvContent += "POSTGRES_DB=$($matches[1])" }

    if ($line -match "^STORAGE_AWS_ENDPOINT_URL=") { $line = "STORAGE_AWS_ENDPOINT_URL=http://$($VM_IP):9000" }
    if ($line -match "^FRONTEND_HOSTNAME=") { $line = "FRONTEND_HOSTNAME=/static" }

    # Domain configuration (synapse.work.gd + IP)
    # Remove port 8080 from allowed hosts and CORS for standard port 80 access
    if ($line -match "^ALLOWED_HOSTS=") { $line = "ALLOWED_HOSTS=localhost,127.0.0.1,$VM_IP,synapse.work.gd,www.synapse.work.gd" }
    
    # CORS: Allow both port 80 (implied) and 8080 just in case
    if ($line -match "^CORS_ALLOWED_ORIGINS=") { $line = "CORS_ALLOWED_ORIGINS=http://localhost:8080,http://$($VM_IP):8080,http://$($VM_IP):9000,http://synapse.work.gd,https://synapse.work.gd" }
    
    # Add CSRF Trusted Origins for the domain (no port needed for 80/443)
    $prodEnvContent += "CSRF_TRUSTED_ORIGINS=http://synapse.work.gd,https://synapse.work.gd,http://www.synapse.work.gd,https://www.synapse.work.gd,http://$($VM_IP):8080"
    
    $prodEnvContent += $line
}
$prodEnvContent | Set-Content "production.env"

# 2. Package and Upload Source (Optimized with Robocopy)
Write-Host "Packaging source (Excluding node_modules/venv)..." -ForegroundColor Yellow
$tempDir = "temp_deploy_pkg_repair"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Use Robocopy for fast mirroring with exclusions
$excludeDirs = @("node_modules", ".git", ".idea", ".vscode", "build", "__pycache__", ".venv", ".nx", "site-packages", "static_build")
$excludeFiles = @("*.pyc", "*.vhdx", "source.zip", "*.log")
robocopy . $tempDir /MIR /XD $excludeDirs /XF $excludeFiles /R:0 /W:0 /NJH /NJS /NDL /NC

# Ensure production.env is included (Robocopy might have missed it if it was just created)
Copy-Item "production.env" -Destination "$tempDir\production.env" -Force

# Zip it
if (Test-Path "source.zip") { Remove-Item "source.zip" -Force }
Write-Host "Zipping..." -ForegroundColor Yellow
Compress-Archive -Path "$tempDir\*" -DestinationPath "source.zip" -Force
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uploading source.zip to VM..." -ForegroundColor Yellow
gcloud compute scp source.zip ${VM_NAME}:./source.zip --zone=$ZONE --quiet

Write-Host "Creating local repair script..." -ForegroundColor Cyan

# We write the bash script to a file first.
# Note: usage of `tr -d '\r'` on the VM ensures Windows line endings from PowerShell don't break bash.
$bashScriptContent = @'
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
'@

# Save to local file
Out-File -FilePath "repair_vm.sh" -InputObject $bashScriptContent -Encoding UTF8 -Force

Write-Host "Uploading repair script to VM..." -ForegroundColor Yellow
gcloud compute scp repair_vm.sh ${VM_NAME}:./repair_vm.sh --zone=$ZONE --quiet

Write-Host "Executing repair script on VM..." -ForegroundColor Yellow
# Critical: Pipe through tr to remove CR characters from Windows-created file
$remoteCommand = "tr -d '\r' < repair_vm.sh > repair_fixed.sh && chmod +x repair_fixed.sh && ./repair_fixed.sh"
gcloud compute ssh $VM_NAME --zone=$ZONE --command=$remoteCommand

Write-Host "Updating Firewall Rules (Allow 80, 443)..." -ForegroundColor Yellow
gcloud compute firewall-rules update allow-synapse-ports --allow="tcp:80,tcp:443,tcp:8080,tcp:9000,tcp:9001"


Write-Host "---------------------------------------------------"
Write-Host "Repair finished. Please verify access at http://34.93.63.53:8080" -ForegroundColor Green
Write-Host "---------------------------------------------------"
