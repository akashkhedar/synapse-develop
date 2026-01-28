#!/bin/bash

# Exit on error
set -e

# ==========================================
# Configuration - Edit these values
# ==========================================
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
APP_NAME="synapse-platform"
REPO_NAME="synapse-repo"
DB_INSTANCE_NAME="synapse-db"
REDIS_INSTANCE_NAME="synapse-redis"
SERVICE_ACCOUNT="synapse-sa"

# ==========================================
# Colors for output
# ==========================================
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Deployment for ${APP_NAME}...${NC}"

# Check dependencies
if ! command -v gcloud &> /dev/null; then
    echo "gcloud command not found. Please install Google Cloud SDK."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "docker command not found. Please install Docker."
    exit 1
fi

# Set Project
echo -e "${GREEN}Setting GCP Project to ${PROJECT_ID}...${NC}"
gcloud config set project $PROJECT_ID

# Enable APIs
echo -e "${GREEN}Enabling required GCP APIs...${NC}"
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com

# Create Artifact Registry Repo
echo -e "${GREEN}Creating/Verifying Artifact Registry Repository...${NC}"
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Synapse Platform"
    echo "Repository created."
else
    echo "Repository exists."
fi

# Configure Docker to authenticate with GCP
echo -e "${GREEN}Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build Docker Image
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${APP_NAME}:latest"
echo -e "${GREEN}Building Docker Image (this may take a while)...${NC}"
# Use the Dockerfile we created
docker build --platform linux/amd64 -t $IMAGE_URI .

# Push Docker Image
echo -e "${GREEN}Pushing Docker Image to Registry...${NC}"
docker push $IMAGE_URI

# Create Cloud SQL Instance (Postgres)
# Note: This is a basic creation. For production, tune machine type, storage, HA, etc.
echo -e "${GREEN}Checking Cloud SQL Instance...${NC}"
if ! gcloud sql instances describe $DB_INSTANCE_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "Creating Cloud SQL instance (this takes time)..."
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password="ChangeMe123!" # CHANGE THIS IN PRODUCTION
else
    echo "Cloud SQL instance exists."
fi

# Create Database and User
echo -e "${GREEN}Ensuring Database and User exist...${NC}"
gcloud sql databases create synapse --instance=$DB_INSTANCE_NAME || true
gcloud sql users create synapse --instance=$DB_INSTANCE_NAME --password="synapse_password" || true

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"

# Check if production.env exists
if [ ! -f "production.env" ]; then
    echo "Warning: production.env not found. Creating a template..."
    cat > production.env <<EOL
DEBUG=False
HOST=https://${APP_NAME}-dot-${PROJECT_ID}.run.app
POSTGRE_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}
POSTGRE_NAME=synapse
POSTGRE_USER=synapse
POSTGRE_PASSWORD=synapse_password
POSTGRE_PORT=5432
DJANGO_SETTINGS_MODULE=synapse.core.settings.synapse
EOL
    echo "Created production.env. Please edit it with your secrets!"
fi

gcloud run deploy $APP_NAME \
    --image $IMAGE_URI \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --env-vars-file=production.env \
    --add-cloudsql-instances="${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"

echo -e "${GREEN}Deployment Complete!${NC}"
echo "Your app should be available at the URL checked above (check Cloud Run console if valid URL is needed)."
