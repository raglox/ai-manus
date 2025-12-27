# 🚀 دليل النشر على Google Cloud Platform

## 📊 معلومات المشروع
- **Project ID**: `gen-lang-client-0415541083`
- **Service Account**: `vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com`
- **Region**: `us-central1` (يمكن تغييره)

## ⚠️ مشكلة الصلاحيات الحالية

Service Account الحالي ليس لديه صلاحيات كافية لتفعيل APIs. تحتاج إلى:

### الحل 1: إعطاء صلاحيات للـ Service Account (موصى به)

قم بتنفيذ الأوامر التالية من **Google Cloud Console** أو من حسابك الشخصي:

```bash
# 1. تفعيل APIs المطلوبة
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  --project=gen-lang-client-0415541083

# 2. إعطاء صلاحيات للـ Service Account
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### الحل 2: استخدام حسابك الشخصي مؤقتاً

```bash
# المصادقة باستخدام حسابك
gcloud auth login
gcloud config set project gen-lang-client-0415541083

# ثم تنفيذ أوامر النشر
```

---

## 🎯 خطوات النشر الكاملة

بعد حل مشكلة الصلاحيات، قم بتنفيذ:

### 1️⃣ إعداد Artifact Registry

```bash
# إنشاء repository لـ Docker images
gcloud artifacts repositories create manus-app \
  --repository-format=docker \
  --location=us-central1 \
  --description="Manus AI application images" \
  --project=gen-lang-client-0415541083

# إعداد Docker للمصادقة
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 2️⃣ بناء ورفع Backend Image

```bash
cd /home/root//webapp/backend

# بناء الصورة
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest .

# رفع الصورة
docker push us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest
```

### 3️⃣ بناء ورفع Frontend Image

```bash
cd /home/root//webapp/frontend

# بناء الصورة
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest .

# رفع الصورة
docker push us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
```

### 4️⃣ إعداد MongoDB و Redis

#### خيار أ: MongoDB Atlas (موصى به)
1. اذهب إلى https://cloud.mongodb.com
2. أنشئ Cluster مجاني
3. احصل على Connection String:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/manus?retryWrites=true&w=majority
   ```

#### خيار ب: Redis Cloud (موصى به)
1. اذهب إلى https://redis.com/try-free/
2. أنشئ Database مجاني
3. احصل على:
   - REDIS_HOST
   - REDIS_PORT
   - REDIS_PASSWORD

### 5️⃣ إنشاء Secrets

```bash
# Blackbox API Key
echo -n "sk-SuSCd8TN7baNnh2EcFnGzw" | gcloud secrets create blackbox-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=gen-lang-client-0415541083

# JWT Secret (توليد عشوائي)
openssl rand -hex 32 | gcloud secrets create jwt-secret-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=gen-lang-client-0415541083

# MongoDB URI
echo -n "YOUR_MONGODB_URI" | gcloud secrets create mongodb-uri \
  --data-file=- \
  --replication-policy="automatic" \
  --project=gen-lang-client-0415541083

# Redis Password (اختياري)
echo -n "YOUR_REDIS_PASSWORD" | gcloud secrets create redis-password \
  --data-file=- \
  --replication-policy="automatic" \
  --project=gen-lang-client-0415541083
```

### 6️⃣ نشر Backend على Cloud Run

```bash
gcloud run deploy manus-backend \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --set-env-vars="LLM_PROVIDER=blackbox,LOG_LEVEL=INFO" \
  --set-secrets="BLACKBOX_API_KEY=blackbox-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest,MONGODB_URI=mongodb-uri:latest" \
  --project=gen-lang-client-0415541083
```

احصل على Backend URL:
```bash
BACKEND_URL=$(gcloud run services describe manus-backend --region=us-central1 --format='value(status.url)' --project=gen-lang-client-0415541083)
echo "Backend URL: $BACKEND_URL"
```

### 7️⃣ نشر Frontend على Cloud Run

```bash
gcloud run deploy manus-frontend \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="BACKEND_URL=$BACKEND_URL" \
  --project=gen-lang-client-0415541083
```

احصل على Frontend URL:
```bash
FRONTEND_URL=$(gcloud run services describe manus-frontend --region=us-central1 --format='value(status.url)' --project=gen-lang-client-0415541083)
echo "Frontend URL: $FRONTEND_URL"
echo "🎉 التطبيق جاهز على: $FRONTEND_URL"
```

---

## 🧪 اختبار النشر

```bash
# اختبار Backend Health
curl $BACKEND_URL/api/v1/health

# اختبار Backend Docs
curl $BACKEND_URL/docs

# فتح Frontend في المتصفح
echo "افتح: $FRONTEND_URL"
```

---

## 💰 التكاليف المتوقعة

### Free Tier شهرياً:
- Cloud Run: 2M requests, 360K vCPU-seconds, 200K GiB-seconds
- Artifact Registry: 0.5 GB storage
- Secret Manager: 6 secrets × 10K accesses

### بعد Free Tier:
- Cloud Run: ~$30-50/شهر (استخدام متوسط)
- MongoDB Atlas: $9/شهر (M0 Shared)
- Redis Cloud: مجاني (30MB)
- Blackbox API: حسب الاستخدام
- **الإجمالي**: ~$40-60/شهر

---

## 🔒 الأمان

### إضافة Custom Domain + SSL (اختياري)

```bash
# 1. التحقق من Domain
gcloud domains verify YOURDOMAIN.com --project=gen-lang-client-0415541083

# 2. ربط Domain بـ Cloud Run
gcloud run domain-mappings create \
  --service=manus-frontend \
  --domain=YOURDOMAIN.com \
  --region=us-central1 \
  --project=gen-lang-client-0415541083

# 3. تحديث DNS Records (اتبع التعليمات المعروضة)
```

---

## 📊 المراقبة والصيانة

### عرض Logs
```bash
# Backend logs
gcloud run services logs read manus-backend --region=us-central1 --project=gen-lang-client-0415541083 --limit=50

# Frontend logs
gcloud run services logs read manus-frontend --region=us-central1 --project=gen-lang-client-0415541083 --limit=50
```

### تحديث التطبيق
```bash
# بعد تغييرات في الكود
cd /home/root//webapp/backend
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:v2 .
docker push us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:v2

gcloud run services update manus-backend \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:v2 \
  --region=us-central1 \
  --project=gen-lang-client-0415541083
```

### Scaling
```bash
# زيادة Max Instances
gcloud run services update manus-backend \
  --max-instances=20 \
  --region=us-central1 \
  --project=gen-lang-client-0415541083
```

---

## 🆘 استكشاف الأخطاء

### مشكلة: Container لا يبدأ
```bash
# فحص logs مفصلة
gcloud run services logs read manus-backend --region=us-central1 --project=gen-lang-client-0415541083 --limit=100

# التحقق من Environment Variables
gcloud run services describe manus-backend --region=us-central1 --format=yaml --project=gen-lang-client-0415541083
```

### مشكلة: خطأ في MongoDB Connection
- تأكد من whitelist IP: `0.0.0.0/0` في MongoDB Atlas
- تأكد من صحة Connection String
- تحقق من username/password

### مشكلة: خطأ في Secrets
```bash
# إعادة إنشاء Secret
gcloud secrets delete jwt-secret-key --project=gen-lang-client-0415541083
openssl rand -hex 32 | gcloud secrets create jwt-secret-key --data-file=- --replication-policy="automatic" --project=gen-lang-client-0415541083
```

---

## ✅ Checklist النشر

- [ ] تفعيل APIs المطلوبة
- [ ] إعطاء صلاحيات لـ Service Account
- [ ] إنشاء Artifact Registry repository
- [ ] بناء ورفع Backend image
- [ ] بناء ورفع Frontend image
- [ ] إعداد MongoDB Atlas
- [ ] إعداد Redis Cloud
- [ ] إنشاء Secrets (Blackbox API Key, JWT Secret, MongoDB URI)
- [ ] نشر Backend على Cloud Run
- [ ] نشر Frontend على Cloud Run
- [ ] اختبار Backend /health endpoint
- [ ] اختبار Frontend UI
- [ ] إعداد Domain + SSL (اختياري)
- [ ] إعداد Monitoring (اختياري)
- [ ] إعداد Backups (اختياري)

---

## 📞 الدعم

في حالة مشاكل:
1. تحقق من Logs: `gcloud run services logs read SERVICE_NAME`
2. تحقق من Status: `gcloud run services describe SERVICE_NAME`
3. تحقق من Quotas: https://console.cloud.google.com/quotas
4. Cloud Run Troubleshooting: https://cloud.google.com/run/docs/troubleshooting

---

**🎯 الخلاصة**: بعد حل مشكلة الصلاحيات، النشر يستغرق ~60-90 دقيقة
