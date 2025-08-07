#!/bin/bash

echo "🔑 Testing SSH Key Authentication for Nate Container..."

echo ""
echo "🧪 Testing local SSH key authentication..."
if ssh -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout=5 nate@localhost -p 2244 "echo 'SSH key authentication successful!'" 2>/dev/null; then
    echo "✅ Local SSH key authentication works!"
else
    echo "❌ Local SSH key authentication failed"
    exit 1
fi

echo ""
echo "📋 Connection Information:"
echo "   Local SSH (key):    ssh nate@localhost -p 2244"
echo "   Remote SSH (key):   ssh nate@106.14.213.46 -p 2244"
echo "   Fallback password:  nate123"

echo ""
echo "🔍 SSH Key Details:"
echo "   Key type: $(head -n1 /home/gaen/.ssh/id_rsa.pub | cut -d' ' -f1)"
echo "   Key fingerprint: $(ssh-keygen -lf /home/gaen/.ssh/id_rsa.pub | cut -d' ' -f2)"
echo "   Key comment: $(tail -c 50 /home/gaen/.ssh/id_rsa.pub)"

echo ""
echo "✅ SSH Key setup complete! You can now connect without a password:"
echo "   ssh nate@localhost -p 2244"
echo "   ssh nate@106.14.213.46 -p 2244"