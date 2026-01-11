#!/bin/bash
# Quick setup script for VM deployment
# This script helps set up the environment and build the Docker image

set -e

echo "=========================================="
echo "🚀 AI Influencer Discovery - VM Setup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created from .env.example"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file with your actual Azure credentials:"
        echo "   nano .env"
        echo ""
        read -p "Press Enter after you've edited .env file to continue..."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Verify .env has required variables
echo ""
echo "🔍 Verifying .env file..."
required_vars=(
    "AZURE_COSMOS_ENDPOINT"
    "AZURE_COSMOS_KEY"
    "AZURE_SEARCH_ENDPOINT"
    "AZURE_SEARCH_KEY"
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env 2>/dev/null || grep -q "^${var}=$" .env 2>/dev/null || grep -q "^${var}=your-" .env 2>/dev/null; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "⚠️  Warning: Some required variables may be missing or not configured:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ All required variables found in .env"
fi

# Secure .env file
echo ""
echo "🔒 Securing .env file permissions..."
chmod 600 .env
echo "✅ .env file permissions set to 600 (read/write for owner only)"

# Check Docker
echo ""
echo "🐳 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    exit 1
fi
echo "✅ Docker is installed"

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "⚠️  Current user is not in docker group. You may need to use 'sudo' for docker commands."
    echo "   To add user to docker group: sudo usermod -aG docker $USER"
    echo "   Then logout and login again."
fi

# Build Docker image
echo ""
echo "🔨 Building Docker image..."
read -p "Build Docker image now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker build -t influencer-api:latest .
    echo ""
    echo "✅ Docker image built successfully!"
    echo "   Image: influencer-api:latest"
else
    echo "⏭️  Skipping Docker build. You can build later with:"
    echo "   docker build -t influencer-api:latest ."
fi

# Ask about running container
echo ""
echo "🚀 Container Deployment"
read -p "Run container now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^influencer-api$"; then
        echo "⚠️  Container 'influencer-api' already exists."
        read -p "Remove and recreate? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop influencer-api 2>/dev/null || true
            docker rm influencer-api 2>/dev/null || true
        else
            echo "⏭️  Skipping container creation."
            exit 0
        fi
    fi
    
    echo "🐳 Starting container..."
    docker run -d \
        --name influencer-api \
        --restart unless-stopped \
        -p 8000:8000 \
        --env-file .env \
        influencer-api:latest
    
    echo ""
    echo "✅ Container started!"
    echo ""
    echo "📊 Container Status:"
    docker ps | grep influencer-api || echo "   Container may still be starting..."
    echo ""
    echo "📝 View logs:"
    echo "   docker logs -f influencer-api"
    echo ""
    echo "🧪 Test health endpoint:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo "🌐 API Documentation:"
    echo "   http://localhost:8000/docs"
else
    echo "⏭️  Skipping container creation. You can run later with:"
    echo "   docker run -d --name influencer-api -p 8000:8000 --env-file .env influencer-api:latest"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📚 For more information, see:"
echo "   - docs/VM_DEPLOYMENT.md"
echo "   - docs/DOCKER.md"
echo ""
