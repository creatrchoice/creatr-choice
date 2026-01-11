# VM Deployment Guide - Manual Docker Build

This guide explains how to clone the repository, configure secrets, and build/run the Docker image manually on a VM.

## Prerequisites

- Azure VM (Ubuntu 20.04/22.04 recommended)
- Docker installed on VM
- Git installed
- Azure credentials (keys, endpoints)

## Step 1: Clone Repository

```bash
# SSH into your VM
ssh azureuser@<your-vm-ip>

# Clone the repository
git clone <your-repo-url>
cd ai-influener-discovery
```

## Step 2: Configure Secrets

**Quick Setup:** Use the automated setup script:
```bash
./scripts/setup_vm.sh
```

Or manually configure secrets using one of the options below:

### Option A: Using .env File (Recommended)

1. **Create `.env` file from template:**

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
# or
vi .env
```

2. **Fill in all required values:**

```env
# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_KEY=your-actual-key-here
AZURE_COSMOS_DATABASE=influencer_db
AZURE_COSMOS_CONTAINER=influencers

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-actual-key-here
AZURE_SEARCH_INDEX_NAME=influencers-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-actual-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-3-large
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Application Settings
CORS_ORIGINS=*
ENVIRONMENT=production
DEBUG=false
```

3. **Secure the .env file:**

```bash
# Set restrictive permissions (only owner can read/write)
chmod 600 .env

# Verify it's not readable by others
ls -la .env
# Should show: -rw------- (600)
```

### Option B: Using Environment Variables

Set environment variables in your shell:

```bash
export AZURE_COSMOS_ENDPOINT="https://your-cosmos.documents.azure.com:443/"
export AZURE_COSMOS_KEY="your-key"
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_DEPLOYMENT_NAME="text-embedding-3-large"
export AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export CORS_ORIGINS="*"
export ENVIRONMENT="production"
export DEBUG="false"
```

**Note:** These will be lost when you close the terminal. To make them persistent, add to `~/.bashrc` or use a `.env` file.

### Option C: Using Docker Secrets (Advanced)

For production, consider using Docker secrets or Azure Key Vault integration.

## Step 2.5: Quick Setup Script (Optional)

For automated setup, use the provided script:

```bash
# Make script executable
chmod +x scripts/setup_vm.sh

# Run setup script
./scripts/setup_vm.sh
```

The script will:
- Create `.env` from template
- Verify required variables
- Secure file permissions
- Build Docker image
- Optionally start the container

## Step 3: Build Docker Image

```bash
# Build the image
docker build -t influencer-api:latest .

# Verify the image was created
docker images | grep influencer-api
```

## Step 4: Run Container

### Using .env File (Recommended)

```bash
docker run -d \
  --name influencer-api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  influencer-api:latest
```

### Using Environment Variables

```bash
docker run -d \
  --name influencer-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e AZURE_COSMOS_ENDPOINT="https://your-cosmos.documents.azure.com:443/" \
  -e AZURE_COSMOS_KEY="your-key" \
  -e AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net" \
  -e AZURE_SEARCH_KEY="your-key" \
  -e AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
  -e AZURE_OPENAI_API_KEY="your-key" \
  -e AZURE_OPENAI_DEPLOYMENT_NAME="text-embedding-3-large" \
  -e AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o" \
  -e AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
  -e CORS_ORIGINS="*" \
  -e ENVIRONMENT="production" \
  -e DEBUG="false" \
  influencer-api:latest
```

### Using Docker Compose

```bash
# Make sure .env file exists
docker-compose up -d

# View logs
docker-compose logs -f
```

## Step 5: Verify Deployment

```bash
# Check container status
docker ps | grep influencer-api

# Check logs
docker logs influencer-api

# Test health endpoint
curl http://localhost:8000/health

# Test API
curl http://localhost:8000/api/v1/influencers/?limit=5
```

## Step 6: Configure Firewall

```bash
# Allow HTTP traffic
sudo ufw allow 8000/tcp

# Or if using nginx reverse proxy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Security Best Practices

### 1. Protect .env File

```bash
# Set restrictive permissions
chmod 600 .env

# Add to .gitignore (should already be there)
echo ".env" >> .gitignore

# Never commit .env to git
git check-ignore .env  # Should return: .env
```

### 2. Use Azure Key Vault (Production)

For production, consider using Azure Key Vault:

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Create Key Vault
az keyvault create \
  --name your-keyvault-name \
  --resource-group your-resource-group \
  --location eastus

# Store secrets
az keyvault secret set \
  --vault-name your-keyvault-name \
  --name "azure-cosmos-key" \
  --value "your-actual-key"

# Retrieve in application (requires Azure Identity)
# The app can use Managed Identity to access Key Vault
```

### 3. Use Systemd Service (Production)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/influencer-api.service
```

```ini
[Unit]
Description=AI Influencer Discovery API
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/influencer-api
ExecStart=/usr/bin/docker start influencer-api
ExecStop=/usr/bin/docker stop influencer-api
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable influencer-api
sudo systemctl start influencer-api
```

## Updating the Application

When you need to update:

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker build -t influencer-api:latest .

# Stop old container
docker stop influencer-api
docker rm influencer-api

# Start new container (with same .env file)
docker run -d \
  --name influencer-api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  influencer-api:latest
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs influencer-api

# Check if .env file exists and has correct format
cat .env | grep -v "^#" | grep -v "^$"

# Test environment variables
docker run --rm --env-file .env influencer-api:latest env | grep AZURE
```

### Connection errors

```bash
# Verify Azure endpoints are correct
curl -I https://your-cosmos.documents.azure.com:443/
curl -I https://your-search.search.windows.net

# Test from container
docker exec -it influencer-api python -c "
from app.core.config import settings
print(f'Cosmos Endpoint: {settings.AZURE_COSMOS_ENDPOINT[:30]}...')
print(f'Search Endpoint: {settings.AZURE_SEARCH_ENDPOINT[:30]}...')
"
```

### Permission errors

```bash
# Ensure .env file has correct permissions
chmod 600 .env
chown $USER:$USER .env
```

## Quick Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_COSMOS_ENDPOINT` | Cosmos DB endpoint URL | `https://xxx.documents.azure.com:443/` |
| `AZURE_COSMOS_KEY` | Cosmos DB primary key | `xxx==` |
| `AZURE_COSMOS_DATABASE` | Database name | `influencer_db` |
| `AZURE_COSMOS_CONTAINER` | Container name | `influencers` |
| `AZURE_SEARCH_ENDPOINT` | AI Search endpoint | `https://xxx.search.windows.net` |
| `AZURE_SEARCH_KEY` | AI Search admin key | `xxx==` |
| `AZURE_SEARCH_INDEX_NAME` | Search index name | `influencers-index` |
| `AZURE_OPENAI_ENDPOINT` | OpenAI endpoint | `https://xxx.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | OpenAI API key | `xxx` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Embedding deployment | `text-embedding-3-large` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment | `gpt-4o` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `CORS_ORIGINS` | Allowed origins | `*` or `https://yourdomain.com` |
| `ENVIRONMENT` | Environment name | `production` |
| `DEBUG` | Debug mode | `false` |

### Common Commands

```bash
# Build image
docker build -t influencer-api:latest .

# Run with .env file
docker run -d --name influencer-api -p 8000:8000 --env-file .env influencer-api:latest

# View logs
docker logs -f influencer-api

# Stop container
docker stop influencer-api

# Remove container
docker rm influencer-api

# Restart container
docker restart influencer-api

# Check container status
docker ps -a | grep influencer-api
```

## Next Steps

- Set up Nginx reverse proxy (see [Docker Deployment Guide](./DOCKER.md))
- Configure SSL/HTTPS with Let's Encrypt
- Set up monitoring and logging
- Configure auto-restart on VM reboot
- Set up automated backups
