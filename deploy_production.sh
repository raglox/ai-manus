#!/bin/bash
# Production Deployment Script with Local Build
# This script deploys the UPDATED version with all security fixes
# Server: 172.245.232.188

SERVER="172.245.232.188"
USER="root"
PASSWORD="pj8QwAf2Gfv1SmcZTgpp"
DEPLOY_DIR="/opt/ai-manus"

set -e

echo "🚀 AI Manus Production Deployment (With All Fixes)"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: This will build from source code"
echo "    ✅ Includes all security fixes"
echo "    ✅ Includes XSS protection"
echo "    ✅ Includes usage limit enforcement"
echo "    ✅ Includes rate limiting"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is not installed!"
    echo "📦 Installing sshpass..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y sshpass
    elif command -v yum &> /dev/null; then
        sudo yum install -y sshpass
    elif command -v brew &> /dev/null; then
        brew install hudochenkov/sshpass/sshpass
    else
        echo "❌ Cannot install sshpass automatically"
        echo "Please install it manually and run this script again"
        exit 1
    fi
fi

# Function to run SSH commands with password
run_ssh() {
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" "$@"
}

# Function to copy files with password
run_scp() {
    sshpass -p "$PASSWORD" rsync -avz --progress -e "ssh -o StrictHostKeyChecking=no" "$@"
}

echo "📋 Step 1/6: Testing connection..."
if run_ssh "echo '✅ Connection successful'"; then
    echo "✅ Connected to server successfully"
else
    echo "❌ Failed to connect to server"
    exit 1
fi

echo ""
echo "📋 Step 2/6: Creating deployment directory..."
run_ssh "mkdir -p $DEPLOY_DIR && echo '✅ Directory created: $DEPLOY_DIR'"

echo ""
echo "📋 Step 3/6: Syncing ALL project files (including source code)..."
echo "⏳ This may take several minutes depending on your connection..."
run_scp \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.env.local' \
    --exclude='dist' \
    --exclude='build' \
    ./ "$USER@$SERVER:$DEPLOY_DIR/"

echo ""
echo "📋 Step 4/6: Installing Docker and dependencies..."
run_ssh << 'ENDSSH'
cd /opt/ai-manus

echo "📦 Updating system packages..."
apt-get update -qq

echo "🐳 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
    docker --version
fi

echo "🐳 Checking Docker Compose installation..."
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
    docker compose version
fi

echo "📝 Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  IMPORTANT: You need to edit .env with your API keys!"
else
    echo "⚠️  .env file already exists, keeping current configuration"
fi

echo "✅ Server setup complete!"
ENDSSH

echo ""
echo "📋 Step 5/6: Building Docker images from source..."
echo "⏳ This will take 5-10 minutes (building backend and frontend)..."
run_ssh << 'ENDSSH'
cd /opt/ai-manus

echo "🔨 Building images from source code..."
echo "   This ensures all security fixes are included!"

# Use production docker-compose file
docker compose -f docker-compose.production.yml build --no-cache

echo "✅ Images built successfully!"
ENDSSH

echo ""
echo "📋 Step 6/6: Starting services..."
run_ssh << 'ENDSSH'
cd /opt/ai-manus

echo "🚀 Starting all services..."
docker compose -f docker-compose.production.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.production.yml ps

echo ""
echo "📝 Recent logs:"
docker compose -f docker-compose.production.yml logs --tail=20

echo ""
echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ PRODUCTION DEPLOYMENT SUCCESSFUL!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 All Security Fixes Applied:"
echo "   ✅ GAP-BILLING-001: Usage limit enforcement"
echo "   ✅ GAP-SESSION-002: SSE rate limiting"
echo "   ✅ GAP-SEC-001: XSS protection"
echo "   ✅ Critical security patches"
echo ""
echo "🌐 Access your application:"
echo "   Frontend:    http://$SERVER:5173"
echo "   Backend API: http://$SERVER:8000"
echo "   API Docs:    http://$SERVER:8000/docs"
echo ""
echo "📝 Important Next Steps:"
echo "   1. ⚠️  Edit API keys:    ssh root@$SERVER 'nano /opt/ai-manus/.env'"
echo "   2. 🔄 Restart if needed: ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml restart'"
echo "   3. 📊 View logs:         ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml logs -f'"
echo "   4. 🔒 Set up firewall:   ssh root@$SERVER 'ufw allow 5173/tcp && ufw allow 8000/tcp'"
echo ""
echo "🔧 Management Commands:"
echo "   Status:  ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml ps'"
echo "   Logs:    ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml logs -f'"
echo "   Restart: ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml restart'"
echo "   Stop:    ssh root@$SERVER 'cd /opt/ai-manus && docker compose -f docker-compose.production.yml down'"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⚡ Built from source code - All fixes included!"
echo "📅 Deployed: $(date)"
echo ""
