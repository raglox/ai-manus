#!/bin/bash
# Emergency Frontend Fix - Direct deployment via IAP tunnel

set -e

echo "════════════════════════════════════════════════════════"
echo "  🚨 EMERGENCY FRONTEND DEPLOYMENT"
echo "════════════════════════════════════════════════════════"
echo ""

PROJECT_ID="gen-lang-client-0415541083"
ZONE="us-central1-a"
VM_NAME="manus-frontend-vm"

# Step 1: Create deployment script locally
cat > /tmp/fix-frontend.sh << 'EOF'
#!/bin/bash
set -e

echo "📦 Downloading frontend package..."
gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz /tmp/

echo "📂 Extracting..."
cd /tmp
tar -xzf frontend-production.tar.gz

echo "💾 Backing up..."
cp -r /usr/share/nginx/html /usr/share/nginx/html_backup 2>/dev/null || true

echo "🚀 Deploying..."
rm -rf /usr/share/nginx/html/*
cp -r /tmp/dist/* /usr/share/nginx/html/

echo "🔒 Setting permissions..."
chown -R nginx:nginx /usr/share/nginx/html/ 2>/dev/null || chown -R www-data:www-data /usr/share/nginx/html/
chmod -R 755 /usr/share/nginx/html/

echo "🔄 Restarting nginx..."
systemctl restart nginx

echo "🧹 Cleaning up..."
rm -rf /tmp/dist /tmp/frontend-production.tar.gz

echo "✅ Deployment complete!"
systemctl status nginx --no-pager | head -3
curl -I http://localhost 2>&1 | head -5
EOF

# Step 2: Upload script to Cloud Storage
echo "📤 Uploading deployment script..."
gsutil cp /tmp/fix-frontend.sh gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/

# Step 3: Use metadata to run command
echo "🔧 Setting up deployment via metadata..."
gcloud compute instances add-metadata ${VM_NAME} \
  --zone=${ZONE} \
  --project=${PROJECT_ID} \
  --metadata=deployment-command="gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/fix-frontend.sh /tmp/ && chmod +x /tmp/fix-frontend.sh && /tmp/fix-frontend.sh"

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Deployment setup complete!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next: Execute deployment on VM"
echo ""
echo "Option 1 - GCP Console (Recommended):"
echo "  1. Go to: https://console.cloud.google.com/compute/instances"
echo "  2. Click 'SSH' on manus-frontend-vm"
echo "  3. Run:"
echo "     gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/fix-frontend.sh /tmp/"
echo "     chmod +x /tmp/fix-frontend.sh"
echo "     sudo /tmp/fix-frontend.sh"
echo ""
echo "Option 2 - Cloud Shell:"
echo "  1. Open Cloud Shell"
echo "  2. Run the commands above"
echo ""
echo "After deployment, test:"
echo "  http://34.121.111.2"
echo "  Login: demo@manus.ai / DemoPass123!"
echo ""
