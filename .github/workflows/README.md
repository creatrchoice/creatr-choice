# Quick Start Guide

## Setup (One-time)

1. **Create Azure Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "github-actions-influencer-api" \
     --role contributor \
     --scopes /subscriptions/{subscription-id} \
     --sdk-auth
   ```
   Copy the JSON output.

2. **Add GitHub Secrets:**
   - Go to: `Settings > Secrets and variables > Actions`
   - Add `AZURE_CREDENTIALS` (paste the JSON from step 1)
   - Add all other required secrets (see GITHUB_ACTIONS.md)

3. **Create Azure Container Registry:**
   ```bash
   az acr create --resource-group influencer-api-rg \
     --name <your-registry-name> --sku Basic
   az acr update --name <your-registry-name> --admin-enabled true
   ```

## Usage

**All workflows run only when tags are created.**

- **Create Tag**: `git tag v1.0.0 && git push origin v1.0.0` → Triggers all workflows
- **Manual**: Actions tab → Select workflow → Run workflow
- **Tag Format**: Use semantic versioning (e.g., `v1.0.0`, `v1.0.1`, `v2.0.0`)

See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md) for detailed documentation.
