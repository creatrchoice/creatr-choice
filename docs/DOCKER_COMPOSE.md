# Docker Compose Guide

This guide explains how to use Docker Compose to run the AI Influencer Discovery API.

## Quick Start

### 1. Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your Azure credentials
nano .env
```

### 2. Start Services

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Docker Compose Files

### `docker-compose.yml` (Base Configuration)

Main configuration file with:
- Service definition
- Environment variables
- Health checks
- Network configuration
- Restart policies

### `docker-compose.prod.yml` (Production Override)

Production-specific settings:
- Resource limits
- Stricter health checks
- Logging configuration
- Production environment variables

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### `docker-compose.override.yml` (Local Development)

For local development overrides (not committed to git):
- Debug mode enabled
- Volume mounts for hot reload
- Development environment

**Usage:**
```bash
# Copy example file
cp docker-compose.override.yml.example docker-compose.override.yml

# Edit as needed
nano docker-compose.override.yml

# Start (override is automatically loaded)
docker-compose up -d
```

## Common Commands

### Start Services

```bash
# Start in detached mode
docker-compose up -d

# Start and rebuild image
docker-compose up -d --build

# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs

```bash
# Follow logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs -f api
```

### Manage Services

```bash
# Restart service
docker-compose restart api

# Stop service
docker-compose stop api

# Start service
docker-compose start api

# View service status
docker-compose ps
```

### Rebuild

```bash
# Rebuild image
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Rebuild and restart
docker-compose up -d --build
```

## Environment Variables

Docker Compose reads from:
1. `.env` file (automatically loaded)
2. Environment variables in `docker-compose.yml`
3. System environment variables

**Priority:** System env vars > docker-compose.yml > .env file

### Using .env File (Recommended)

```bash
# Create .env file
cp .env.example .env

# Edit with your values
nano .env

# Start services (automatically uses .env)
docker-compose up -d
```

### Using Environment Variables

```bash
# Set environment variables
export AZURE_COSMOS_ENDPOINT="https://..."
export AZURE_COSMOS_KEY="..."

# Start services
docker-compose up -d
```

## Configuration Options

### Port Configuration

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Host:Container
```

Or use environment variable:

```bash
PORT=8080 docker-compose up -d
```

### Resource Limits

Uncomment resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Logging

Configure logging in `docker-compose.prod.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Volume Mounts

For development with hot reload:

```yaml
volumes:
  - .:/app
  - /app/venv  # Exclude venv
```

## Production Deployment

### Using Production Configuration

```bash
# Start with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or create a production .env file
cp .env.example .env.prod
# Edit .env.prod with production values
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Using Pre-built Image

If you have a pre-built image in a registry:

```yaml
# In docker-compose.prod.yml, uncomment:
image: your-registry.azurecr.io/influencer-api:latest
# And comment out:
# build:
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check if .env file exists
ls -la .env

# Verify environment variables
docker-compose config
```

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### Environment Variables Not Loading

```bash
# Verify .env file format (no spaces around =)
cat .env | grep AZURE_COSMOS

# Check docker-compose config
docker-compose config | grep AZURE_COSMOS

# Test with explicit env file
docker-compose --env-file .env config
```

### Health Check Failing

```bash
# Check container logs
docker-compose logs api

# Test health endpoint manually
docker-compose exec api curl http://localhost:8000/health

# Increase health check start period
healthcheck:
  start_period: 60s  # Increase if app takes longer to start
```

## Examples

### Development Setup

```bash
# 1. Create .env file
cp .env.example .env
nano .env

# 2. Create override for development
cp docker-compose.override.yml.example docker-compose.override.yml
nano docker-compose.override.yml

# 3. Start services
docker-compose up -d

# 4. View logs
docker-compose logs -f api
```

### Production Setup

```bash
# 1. Create production .env
cp .env.example .env.prod
nano .env.prod

# 2. Start with production config
docker-compose --env-file .env.prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d

# 3. Verify
docker-compose ps
curl http://localhost:8000/health
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose build api
docker-compose up -d
```

## Best Practices

1. **Never commit .env files** - Already in .gitignore
2. **Use docker-compose.prod.yml for production** - Separate configs
3. **Set resource limits** - Prevent resource exhaustion
4. **Configure logging** - Rotate logs to prevent disk fill
5. **Use health checks** - Automatic container restart on failure
6. **Set restart policies** - Automatic recovery from crashes

## Integration with Systemd

Create a systemd service for auto-start:

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
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable influencer-api
sudo systemctl start influencer-api
```
