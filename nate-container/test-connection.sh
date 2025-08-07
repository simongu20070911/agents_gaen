#!/bin/bash

echo "🧪 Testing Nate Container Connection..."

# Test container status
echo "📦 Container Status:"
docker ps | grep nate-dev-container

echo ""
echo "🌐 Network Connectivity Test:"
echo "Local SSH: ssh nate@localhost -p 2244"
echo "Remote SSH: ssh nate@106.14.213.46 -p 2244"
echo "Password: nate123"

echo ""
echo "🔧 Testing container services..."

# Test SSH connectivity locally
if nc -z localhost 2244; then
    echo "✅ Local SSH port 2244 is accessible"
else
    echo "❌ Local SSH port 2244 is not accessible"
fi

# Test Node.js version
echo ""
echo "🟢 Node.js version in container:"
docker exec -u nate nate-dev-container node --version

# Test Claude Code installation
echo ""
echo "🤖 Claude Code installation check:"
docker exec -u nate nate-dev-container bash -c "export PATH=~/.npm-global/bin:\$PATH && which claude"

# Test GPU access
echo ""
echo "🎮 GPU Access Test:"
docker exec nate-dev-container nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "❌ GPU access failed"

# Show resource usage
echo ""
echo "📊 Container Resource Usage:"
docker stats nate-dev-container --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "🎉 Test completed! You can now:"
echo "   1. SSH into the container: ssh nate@localhost -p 2244"
echo "   2. Or from remote: ssh nate@106.14.213.46 -p 2244" 
echo "   3. Run Claude Code: claude (after SSH login)"
echo "   4. Use GPU: nvidia-smi"