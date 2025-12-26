#!/bin/bash
# AI Manus Deployment Script
# Server: 172.245.232.188
# User: root

set -e

SERVER="172.245.232.188"
USER="root"
PROJECT_NAME="ai-manus"
DEPLOY_DIR="/opt/$PROJECT_NAME"

echo "🚀 AI Manus Deployment Script"
echo "================================"
echo "Server: $SERVER"
echo "Deploy Directory: $DEPLOY_DIR"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Creating deployment directory on server...${NC}"
ssh $USER@$SERVER "mkdir -p $DEPLOY_DIR && cd $DEPLOY_DIR && pwd"

echo -e "${YELLOW}Step 2: Syncing project files to server...${NC}"
rsync -avz --progress \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='*.pyc' \
  --exclude='.env.local' \
  --exclude='dist' \
  --exclude='build' \
  ./ $USER@$SERVER:$DEPLOY_DIR/

echo -e "${YELLOW}Step 3: Setting up environment on server...${NC}"
ssh $USER@$SERVER << 'ENDSSH'
cd /opt/ai-manus

# Update system
echo "📦 Updating system packages..."
apt-get update -qq

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not installed
if ! docker compose version &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Verify installations
echo "✅ Docker version:"
docker --version
echo "✅ Docker Compose version:"
docker compose version

# Copy example env if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
fi

echo "✅ Environment setup complete!"
ENDSSH

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo "🔧 Next Steps:"
echo "1. SSH to the server: ssh $USER@$SERVER"
echo "2. Navigate to: cd $DEPLOY_DIR"
echo "3. Edit .env file: nano .env"
echo "4. Start services: docker compose up -d"
echo "5. View logs: docker compose logs -f"
echo ""
echo "📊 Monitor the application:"
echo "- Frontend: http://$SERVER:5173"
echo "- Backend API: http://$SERVER:8000"
echo ""

