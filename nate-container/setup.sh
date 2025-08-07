#!/bin/bash

# Nate Container Setup Script
# This script builds and runs the Nate development container

set -e

echo "🚀 Setting up Nate's Docker Container..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if NVIDIA runtime is available
if ! docker info | grep -q "nvidia"; then
    echo "⚠️  NVIDIA runtime not detected. GPU support may not work."
fi

# Build the container
echo "🔨 Building container image..."
docker compose build

# Create storage directories if they don't exist
echo "📁 Creating storage directories..."
mkdir -p /home/gaen/nate-container-data
mkdir -p /home/gaen/nate-container-projects

# Set permissions
chmod 755 /home/gaen/nate-container-data
chmod 755 /home/gaen/nate-container-projects

# Start the container
echo "🚀 Starting container..."
docker compose up -d

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 10

# Check if container is running
if docker ps | grep -q "nate-dev-container"; then
    echo "✅ Container is running successfully!"
    
    # Display connection information
    echo ""
    echo "📋 Connection Information:"
    echo "   Local SSH:    ssh nate@localhost -p 2244"
    echo "   Remote SSH:   ssh nate@106.14.213.46 -p 2244"
    echo "   Password:     nate123"
    echo ""
    echo "💾 Persistent Storage:"
    echo "   Data:         /home/nate/data (maps to /home/gaen/nate-container-data)"
    echo "   Projects:     /home/nate/projects (maps to /home/gaen/nate-container-projects)"
    echo ""
    echo "🎮 GPU Information:"
    docker exec nate-dev-container nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "   GPU access verification failed"
    
else
    echo "❌ Container failed to start. Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now connect to the container."