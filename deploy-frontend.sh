#!/bin/bash
# Manus Frontend Deployment Script
# Deploy built frontend to production VM

set -e  # Exit on error

echo "============================================"
echo "Manus AI Frontend Deployment"
echo "============================================"
echo ""

# Configuration
PROJECT_ID="gen-lang-client-0415541083"
ZONE="us-central1-a"
VM_NAME="manus-frontend-vm"
FRONTEND_DIR="/home/root/webapp/frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if dist folder exists
echo "📦 Step 1: Checking build artifacts..."
if [ ! -d "$FRONTEND_DIR/dist" ]; then
    echo -e "${RED}❌ Error: dist/ folder not found${NC}"
    echo "Please run 'npm run build' first"
    exit 1
fi
echo -e "${GREEN}✅ Build artifacts found${NC}"
echo ""

# Step 2: Create tarball
echo "📦 Step 2: Creating deployment package..."
cd "$FRONTEND_DIR"
tar -czf /tmp/manus-frontend-dist.tar.gz dist/
echo -e "${GREEN}✅ Package created: /tmp/manus-frontend-dist.tar.gz${NC}"
echo ""

# Step 3: Upload to VM
echo "📤 Step 3: Uploading to production VM..."
export PATH="/tmp/google-cloud-sdk/bin:$PATH"
gcloud compute scp /tmp/manus-frontend-dist.tar.gz \
    ${VM_NAME}:/tmp/ \
    --zone=${ZONE} \
    --project=${PROJECT_ID} \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Upload successful${NC}"
else
    echo -e "${RED}❌ Upload failed${NC}"
    exit 1
fi
echo ""

# Step 4: Deploy on VM
echo "🚀 Step 4: Deploying on production VM..."
gcloud compute ssh ${VM_NAME} \
    --zone=${ZONE} \
    --project=${PROJECT_ID} \
    --command='
        set -e
        echo "  → Extracting package..."
        cd /tmp
        tar -xzf manus-frontend-dist.tar.gz
        
        echo "  → Backing up current deployment..."
        if [ -d /usr/share/nginx/html_backup ]; then
            rm -rf /usr/share/nginx/html_backup
        fi
        cp -r /usr/share/nginx/html /usr/share/nginx/html_backup || true
        
        echo "  → Deploying new version..."
        rm -rf /usr/share/nginx/html/*
        cp -r /tmp/dist/* /usr/share/nginx/html/
        
        echo "  → Restarting nginx..."
        systemctl restart nginx
        
        echo "  → Cleaning up..."
        rm -rf /tmp/dist /tmp/manus-frontend-dist.tar.gz
        
        echo "  → Verifying deployment..."
        sleep 2
        curl -s -I http://localhost | head -1
    '

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi
echo ""

# Step 5: Verify
echo "🧪 Step 5: Verifying deployment..."
sleep 3
FRONTEND_IP="34.121.111.2"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${FRONTEND_IP})

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
    echo "   URL: http://${FRONTEND_IP}"
else
    echo -e "${YELLOW}⚠️  Warning: Frontend returned status $HTTP_STATUS${NC}"
fi
echo ""

# Cleanup
echo "🧹 Cleaning up local artifacts..."
rm -f /tmp/manus-frontend-dist.tar.gz
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Success summary
echo "============================================"
echo "🎉 Deployment Complete!"
echo "============================================"
echo ""
echo "📋 Summary:"
echo "  • Frontend URL: http://${FRONTEND_IP}"
echo "  • Backend API: https://manus-backend-247096226016.us-central1.run.app"
echo "  • Test User: demo@manus.ai"
echo "  • Password: DemoPass123!"
echo ""
echo "🧪 Next Steps:"
echo "  1. Open http://${FRONTEND_IP} in your browser"
echo "  2. Login with demo credentials"
echo "  3. Test agent creation and chat functionality"
echo ""
echo "📚 Documentation: /home/root/webapp/FINAL_SYSTEM_DELIVERY.md"
echo ""
