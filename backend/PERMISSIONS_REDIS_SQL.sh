#!/bin/bash
# صلاحيات Redis Memorystore + Cloud SQL

PROJECT_ID="gen-lang-client-0415541083"
SERVICE_ACCOUNT="vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com"

echo "🔄 تفعيل APIs..."
gcloud services enable \
  redis.googleapis.com \
  sqladmin.googleapis.com \
  servicenetworking.googleapis.com \
  vpcaccess.googleapis.com \
  --project=$PROJECT_ID

echo ""
echo "🔄 إضافة الصلاحيات..."

# Redis Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/redis.admin" \
  --quiet && echo "✅ Redis Admin"

# Cloud SQL Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.admin" \
  --quiet && echo "✅ Cloud SQL Admin"

# VPC Access Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/vpcaccess.admin" \
  --quiet && echo "✅ VPC Access Admin"

# Service Networking Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/servicenetworking.networksAdmin" \
  --quiet && echo "✅ Service Networking Admin"

# Network Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/compute.networkAdmin" \
  --quiet && echo "✅ Compute Network Admin"

echo ""
echo "✅✅✅ جميع الصلاحيات تم إضافتها بنجاح! ✅✅✅"
