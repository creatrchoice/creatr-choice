# GitHub Actions Workflows

This repository includes comprehensive CI/CD workflows for automated testing, building, and deployment.

## Workflows Overview

### 1. **CI - Test and Build** (`.github/workflows/ci.yml`)

Runs when tags are created (e.g., `v1.0.0`).

**Jobs:**
- **Lint Code**: Runs Ruff linter and Black formatter checks
- **Run Tests**: Executes pytest tests (if available)
- **Build Docker Image**: Builds and tests the Docker image
- **Security Scan**: Runs Trivy vulnerability scanner

**Triggers:**
- Push tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

### 2. **CD - Deploy to Azure Container Instances** (`.github/workflows/cd-azure-container-instances.yml`)

Deploys the application to Azure Container Instances.

**Features:**
- Extracts tag name for image reference
- Creates or updates Azure Container Instance
- Performs health check
- Supports manual deployment with environment selection

**Note:** Image push is disabled. You must push the Docker image to ACR manually before deployment.

**Triggers:**
- Push tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

### 3. **CD - Deploy to Azure Container Apps** (`.github/workflows/cd-azure-container-apps.yml`)

Deploys the application to Azure Container Apps (recommended for production).

**Features:**
- Extracts tag name for image reference
- Creates or updates Azure Container App
- Auto-scaling (1-10 replicas)
- HTTPS enabled by default
- Performs health check

**Note:** Image push is disabled. You must push the Docker image to ACR manually before deployment.

**Triggers:**
- Push tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

### 4. **Build Docker Image** (`.github/workflows/docker-build-push.yml`)

Builds Docker images (push is disabled - you'll push manually).

**Features:**
- Builds Docker image with tag name
- Tag-based image tagging
- Cache optimization
- Does NOT push to registry (manual push required)

**Triggers:**
- Push tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Azure Authentication
- `AZURE_CREDENTIALS`: Azure service principal credentials (JSON)
  ```json
  {
    "clientId": "...",
    "clientSecret": "...",
    "subscriptionId": "...",
    "tenantId": "..."
  }
  ```

### Azure Container Registry
- `AZURE_ACR_NAME`: Your ACR registry name (e.g., `myregistry`)
- `AZURE_ACR_USERNAME`: ACR admin username
- `AZURE_ACR_PASSWORD`: ACR admin password

### Application Environment Variables
- `AZURE_COSMOS_ENDPOINT`: Cosmos DB endpoint
- `AZURE_COSMOS_KEY`: Cosmos DB key
- `AZURE_COSMOS_DATABASE`: Database name
- `AZURE_COSMOS_CONTAINER`: Container name
- `AZURE_SEARCH_ENDPOINT`: Azure AI Search endpoint
- `AZURE_SEARCH_KEY`: Azure AI Search key
- `AZURE_SEARCH_INDEX_NAME`: Search index name
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Embedding deployment name
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: Chat model deployment name
- `AZURE_OPENAI_API_VERSION`: API version
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

## Setting Up Azure Service Principal

Create a service principal for GitHub Actions:

```bash
# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-influencer-api" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Copy the JSON output and add it as AZURE_CREDENTIALS secret
```

## Setting Up Azure Container Registry

```bash
# Create resource group
az group create --name influencer-api-rg --location eastus

# Create Azure Container Registry
az acr create \
  --resource-group influencer-api-rg \
  --name <your-registry-name> \
  --sku Basic

# Enable admin user
az acr update --name <your-registry-name> --admin-enabled true

# Get credentials
az acr credential show --name <your-registry-name>
```

## Workflow Usage

### Automatic Deployment

**All workflows now run only when tags are created.**

1. **Create and push a tag**: This triggers all CI/CD workflows
   ```bash
   # Create a tag
   git tag v1.0.0
   
   # Push the tag (this triggers workflows)
   git push origin v1.0.0
   ```

2. **Tag naming convention**: Use semantic versioning
   - `v1.0.0` - Major release
   - `v1.0.1` - Patch release
   - `v1.1.0` - Minor release
   - `v2.0.0` - Major version bump

### Manual Image Push

**Image push is disabled in workflows. You must push images manually:**

```bash
# 1. Build image locally (or use the built image from CI)
docker build -t influencer-api:v1.0.0 .

# 2. Tag for ACR
docker tag influencer-api:v1.0.0 <registry-name>.azurecr.io/influencer-api:v1.0.0

# 3. Login to ACR
az acr login --name <registry-name>

# 4. Push to ACR
docker push <registry-name>.azurecr.io/influencer-api:v1.0.0
```

**After pushing, the CD workflows will use the image from ACR for deployment.**

### Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select the workflow (e.g., "CD - Deploy to Azure Container Apps")
3. Click **Run workflow**
4. Select environment (production/staging)
5. Click **Run workflow**

### Viewing Workflow Status

- Go to **Actions** tab to see all workflow runs
- Click on a workflow run to see detailed logs
- Check deployment summary at the end of each run

## Environment Protection

For production deployments, set up environment protection rules:

1. Go to **Settings > Environments**
2. Create `production` environment
3. Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (only `main`)

## Troubleshooting

### Workflow Fails at Build Step

- Check Dockerfile syntax
- Verify all dependencies in `requirements.txt`
- Check build logs for specific errors

### Deployment Fails

- Verify all secrets are set correctly
- Check Azure service principal permissions
- Verify resource group and resources exist
- Check Azure Container Registry credentials

### Health Check Fails

- Verify environment variables are set correctly
- Check application logs in Azure Portal
- Ensure `/health` endpoint is accessible
- Check firewall/network rules

### Authentication Errors

- Verify `AZURE_CREDENTIALS` secret is valid JSON
- Check service principal has correct permissions
- Ensure service principal hasn't expired

## Best Practices

1. **Use Environments**: Set up separate environments for staging and production
2. **Review Deployments**: Require manual approval for production
3. **Monitor Workflows**: Set up notifications for failed workflows
4. **Tag Releases**: Use semantic versioning tags for releases
5. **Test Locally**: Test Docker builds locally before pushing
6. **Secure Secrets**: Never commit secrets to repository
7. **Use Branch Protection**: Protect `main` branch with required checks

## Workflow Customization

### Adjust Worker Count

Edit the Dockerfile CMD to change worker count:
```dockerfile
CMD ["gunicorn", "main:app", "--workers", "8", ...]
```

### Change Resource Limits

Edit the deployment workflows to adjust:
- CPU cores
- Memory
- Replica counts (Container Apps)
- Auto-scaling rules

### Add Custom Tests

Add test steps in `ci.yml`:
```yaml
- name: Run custom tests
  run: |
    python scripts/test_custom.py
```

## CI/CD Pipeline Flow

```
Create and push tag (v1.0.0)
    ↓
CI Workflow
    ├── Lint Code
    ├── Run Tests
    ├── Build Docker Image
    └── Security Scan
    ↓
CD Workflow
    ├── Extract Tag Name
    ├── Note: Image push disabled (manual push required)
    ├── Deploy to Azure (uses image from ACR)
    └── Health Check
    ↓
Deployment Complete ✅
```

**Note**: 
- Workflows only run when you create and push tags, not on regular commits.
- **Image push is disabled** - you must push the Docker image to ACR manually before deployment.

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Docker Buildx](https://docs.docker.com/buildx/)
