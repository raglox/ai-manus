#!/bin/bash

# 🚀 Automated Deployment Script for Google Cloud Run
# Project: gen-lang-client-0415541083
# This script completes the deployment after MongoDB & Redis credentials are provided

set -e  # Exit on error

echo "════════════════════════════════════════════════════════"
echo "🚀 Manus AI - Google Cloud Run Deployment"
echo "════════════════════════════════════════════════════════"
echo ""

# Setup PATH
export PATH="/home/root/google-cloud-sdk/bin:$PATH"

# Project variables
PROJECT_ID="gen-lang-client-0415541083"
REGION="us-central1"
BACKEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/manus-app/backend:latest"
FRONTEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/manus-app/frontend:latest"

echo "📋 Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Backend Image: $BACKEND_IMAGE"
echo "  Frontend Image: $FRONTEND_IMAGE"
echo ""

# Check if credentials are provided
if [ -z "$MONGODB_URI" ]; then
    echo "❌ ERROR: MONGODB_URI environment variable not set"
    echo ""
    echo "Please set MongoDB Atlas connection string:"
    echo "  export MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/manus'"
    echo ""
    exit 1
fi

if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PORT" ] || [ -z "$REDIS_PASSWORD" ]; then
    echo "❌ ERROR: Redis credentials not set"
    echo ""
    echo "Please set Redis Cloud credentials:"
    echo "  export REDIS_HOST='redis-xxxxx.redis.cloud'"
    echo "  export REDIS_PORT='12345'"
    echo "  export REDIS_PASSWORD='xxxxxxxxxx'"
    echo ""
    exit 1
fi

echo "✅ MongoDB URI: ${MONGODB_URI:0:30}..."
echo "✅ Redis Host: $REDIS_HOST"
echo "✅ Redis Port: $REDIS_PORT"
echo ""

# Create MongoDB URI secret
echo "📝 Creating MongoDB URI secret..."
echo -n "$MONGODB_URI" | gcloud secrets create mongodb-uri \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID 2>/dev/null || \
echo -n "$MONGODB_URI" | gcloud secrets versions add mongodb-uri --data-file=- --project=$PROJECT_ID

echo "✅ MongoDB URI secret created/updated"

# Create Redis password secret
echo "📝 Creating Redis password secret..."
echo -n "$REDIS_PASSWORD" | gcloud secrets create redis-password \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID 2>/dev/null || \
echo -n "$REDIS_PASSWORD" | gcloud secrets versions add redis-password --data-file=- --project=$PROJECT_ID

echo "✅ Redis password secret created/updated"

# Grant IAM permissions
echo "🔐 Granting IAM permissions..."
gcloud secrets add-iam-policy-binding mongodb-uri \
  --member="serviceAccount:247096226016-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID --quiet

gcloud secrets add-iam-policy-binding redis-password \
  --member="serviceAccount:247096226016-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID --quiet

echo "✅ IAM permissions granted"
echo ""

# Deploy Backend
echo "🚀 Deploying Backend to Cloud Run..."
gcloud run deploy manus-backend \
  --image=$BACKEND_IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=8000 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --set-env-vars="LLM_PROVIDER=blackbox,LOG_LEVEL=INFO,MONGODB_DATABASE=manus,REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT,REDIS_DB=0" \
  --set-secrets="BLACKBOX_API_KEY=blackbox-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest,MONGODB_URI=mongodb-uri:latest,REDIS_PASSWORD=redis-password:latest" \
  --project=$PROJECT_ID

echo "✅ Backend deployed successfully"
echo ""

# Get Backend URL
BACKEND_URL=$(gcloud run services describe manus-backend \
  --region=$REGION \
  --format='value(status.url)' \
  --project=$PROJECT_ID)

echo "🎯 Backend URL: $BACKEND_URL"
echo ""

# Test Backend Health
echo "🏥 Testing Backend health endpoint..."
curl -s "$BACKEND_URL/api/v1/health" | head -3 || echo "⚠️ Health check failed (may need warmup)"
echo ""

# Deploy Frontend
echo "🚀 Deploying Frontend to Cloud Run..."
gcloud run deploy manus-frontend \
  --image=$FRONTEND_IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="BACKEND_URL=$BACKEND_URL" \
  --project=$PROJECT_ID

echo "✅ Frontend deployed successfully"
echo ""

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe manus-frontend \
  --region=$REGION \
  --format='value(status.url)' \
  --project=$PROJECT_ID)

echo "════════════════════════════════════════════════════════"
echo "🎉 Deployment Complete!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📱 Application URLs:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "  API Docs: $BACKEND_URL/docs"
echo "  Health:   $BACKEND_URL/api/v1/health"
echo ""
echo "🧪 Test Commands:"
echo "  # Test backend health"
echo "  curl $BACKEND_URL/api/v1/health"
echo ""
echo "  # Test backend docs"
echo "  curl $BACKEND_URL/docs"
echo ""
echo "  # Open frontend in browser"
echo "  open $FRONTEND_URL  # macOS"
echo "  xdg-open $FRONTEND_URL  # Linux"
echo ""
echo "✅ All services deployed and running!"
echo "════════════════════════════════════════════════════════"
