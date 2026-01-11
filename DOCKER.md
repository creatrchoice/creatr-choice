# Docker Deployment Guide

This guide explains how to build and run the AI Influencer Discovery API using Docker.

## Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- Environment variables configured

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t influencer-api:latest .
```

### 2. Run with Docker

```bash
# Using environment variables from .env file
docker run -d \
  --name influencer-api \
  -p 8000:8000 \
  --env-file .env \
  influencer-api:latest
```

### 3. Run with Docker Compose (Recommended)

```bash
# Make sure .env file exists with all required variables
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Environment Variables

Create a `.env` file in the project root with all required variables:

```env
# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_KEY=your-key
AZURE_COSMOS_DATABASE=influencer_db
AZURE_COSMOS_CONTAINER=influencers

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX_NAME=influencers-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-3-large
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Application Settings
CORS_ORIGINS=*
ENVIRONMENT=production
DEBUG=false
```

## Docker Commands

### Build

```bash
# Build image
docker build -t influencer-api:latest .

# Build with specific tag
docker build -t influencer-api:v1.0.0 .

# Build without cache
docker build --no-cache -t influencer-api:latest .
```

### Run

```bash
# Run in foreground
docker run -p 8000:8000 --env-file .env influencer-api:latest

# Run in background
docker run -d -p 8000:8000 --env-file .env --name influencer-api influencer-api:latest

# Run with specific environment variables
docker run -d \
  -p 8000:8000 \
  -e AZURE_COSMOS_ENDPOINT="https://..." \
  -e AZURE_COSMOS_KEY="..." \
  ... \
  influencer-api:latest
```

### Manage Container

```bash
# View logs
docker logs influencer-api
docker logs -f influencer-api  # Follow logs

# Stop container
docker stop influencer-api

# Start container
docker start influencer-api

# Restart container
docker restart influencer-api

# Remove container
docker rm influencer-api

# Execute command in running container
docker exec -it influencer-api /bin/bash
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View status
docker-compose ps
```

## Testing

After starting the container, test the API:

```bash
# Health check
curl http://localhost:8000/health

# API endpoint
curl http://localhost:8000/api/v1/influencers/?limit=5

# API documentation
open http://localhost:8000/docs
```

## Production Deployment

### Azure Container Instances (ACI)

```bash
# Login to Azure
az login

# Create resource group
az group create --name influencer-api-rg --location eastus

# Create container instance
az container create \
  --resource-group influencer-api-rg \
  --name influencer-api \
  --image influencer-api:latest \
  --dns-name-label influencer-api \
  --ports 8000 \
  --environment-variables \
    AZURE_COSMOS_ENDPOINT="..." \
    AZURE_COSMOS_KEY="..." \
    ...
```

### Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <registry-name> --image influencer-api:latest .

# Create container app
az containerapp create \
  --name influencer-api \
  --resource-group influencer-api-rg \
  --image <registry-name>.azurecr.io/influencer-api:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    AZURE_COSMOS_ENDPOINT="..." \
    ...
```

### Azure Kubernetes Service (AKS)

```bash
# Build and push to ACR
az acr build --registry <registry-name> --image influencer-api:latest .

# Create deployment
kubectl create deployment influencer-api \
  --image=<registry-name>.azurecr.io/influencer-api:latest

# Expose service
kubectl expose deployment influencer-api \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8000
```

## Image Optimization

The Dockerfile uses multi-stage builds to:
- Reduce final image size
- Separate build dependencies from runtime
- Improve security with non-root user

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs influencer-api

# Check if port is already in use
lsof -i :8000

# Run interactively to debug
docker run -it --env-file .env influencer-api:latest /bin/bash
```

### Environment variables not loading

- Ensure `.env` file exists and has correct format
- Check variable names match exactly (case-sensitive)
- Verify no extra spaces or quotes in `.env` file

### Connection errors

- Verify all Azure service endpoints are correct
- Check API keys are valid
- Ensure network connectivity from container

### Performance issues

- Adjust worker count in Dockerfile CMD (currently 4)
- Monitor resource usage: `docker stats influencer-api`
- Consider increasing container resources

## Security Best Practices

1. **Never commit `.env` file** - Use secrets management
2. **Use non-root user** - Already configured in Dockerfile
3. **Keep images updated** - Regularly rebuild with latest base images
4. **Scan for vulnerabilities** - Use `docker scan influencer-api:latest`
5. **Use secrets** - In production, use Azure Key Vault or Docker secrets

## Health Checks

The container includes a health check that:
- Runs every 30 seconds
- Checks `/health` endpoint
- Allows 40 seconds for startup
- Retries 3 times before marking unhealthy

View health status:
```bash
docker inspect --format='{{.State.Health.Status}}' influencer-api
```
