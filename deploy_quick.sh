#!/bin/bash
# Quick Deployment Script for AI Manus
# This script uses sshpass for password authentication

SERVER="172.245.232.188"
USER="root"
PASSWORD="pj8QwAf2Gfv1SmcZTgpp"
DEPLOY_DIR="/opt/ai-manus"

echo "🚀 AI Manus Quick Deployment"
echo "============================="
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
        echo "Please install it manually:"
        echo "  Ubuntu/Debian: sudo apt-get install sshpass"
        echo "  CentOS/RHEL: sudo yum install sshpass"
        echo "  macOS: brew install hudochenkov/sshpass/sshpass"
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

echo "📋 Step 1/5: Testing connection..."
if run_ssh "echo '✅ Connection successful'"; then
    echo "✅ Connected to server successfully"
else
    echo "❌ Failed to connect to server"
    exit 1
fi

echo ""
echo "📋 Step 2/5: Creating deployment directory..."
run_ssh "mkdir -p $DEPLOY_DIR && echo '✅ Directory created: $DEPLOY_DIR'"

echo ""
echo "📋 Step 3/5: Syncing project files (this may take a few minutes)..."
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
echo "📋 Step 4/5: Installing Docker and dependencies..."
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
fi

echo "🐳 Checking Docker Compose installation..."
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

echo "📝 Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "⚠️  .env file already exists, keeping current configuration"
fi

echo "✅ Server setup complete!"
ENDSSH

echo ""
echo "📋 Step 5/5: Starting services..."
run_ssh << 'ENDSSH'
cd /opt/ai-manus

echo "🐳 Pulling Docker images..."
docker compose pull

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access your application:"
echo "   Frontend:    http://$SERVER:5173"
echo "   Backend API: http://$SERVER:8000"
echo "   API Docs:    http://$SERVER:8000/docs"
echo ""
echo "📝 Important Notes:"
echo "   1. Edit configuration: ssh root@$SERVER 'nano /opt/ai-manus/.env'"
echo "   2. View logs:         ssh root@$SERVER 'cd /opt/ai-manus && docker compose logs -f'"
echo "   3. Restart services:  ssh root@$SERVER 'cd /opt/ai-manus && docker compose restart'"
echo ""
echo "🔧 Quick Commands:"
echo "   ssh root@$SERVER                                    # Connect to server"
echo "   ssh root@$SERVER 'cd /opt/ai-manus && docker compose ps'     # Check status"
echo "   ssh root@$SERVER 'cd /opt/ai-manus && docker compose logs'   # View logs"
echo ""
echo "════════════════════════════════════════════════════════════════"
