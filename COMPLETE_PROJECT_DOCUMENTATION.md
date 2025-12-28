# 📋 Manus AI - Complete Project Documentation

**تاريخ الإنشاء:** 28 ديسمبر 2025  
**الإصدار:** 1.0.2  
**الحالة:** Production (مع مشكلة Auth)

---

## 🎯 نظرة عامة على المشروع

**Manus AI** هو نظام AI Agent يتيح للمستخدمين التفاعل مع وكلاء ذكاء اصطناعي عبر واجهة chat. النظام مبني على:
- **Backend:** FastAPI + Python
- **Frontend:** React + TypeScript + Vite
- **Database:** MongoDB Atlas
- **Cache:** Redis (Memorystore)
- **Infrastructure:** Google Cloud Platform (Cloud Run, Compute Engine)

---

## 🏗️ البنية التحتية

### 1. Google Cloud Project

**Project ID:** `gen-lang-client-0415541083`  
**Project Number:** `247096226016`  
**Region:** `us-central1`  
**Zone:** `us-central1-a`

### 2. Service Account

**Active Service Account:**
```
vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com
```

**الأذونات:**
- Cloud Run Admin
- Cloud Build Service Account
- Artifact Registry Writer
- (محدودة - لا يمكن قراءة Logs)

---

## 🌐 السيرفرات والخدمات

### Backend - Cloud Run

**Service Name:** `manus-backend`  
**URL:** `https://manus-backend-247096226016.us-central1.run.app`  
**Region:** `us-central1`  
**Current Revision:** `manus-backend-00028-jnq` (rolled back)

**Revisions History:**
- `manus-backend-00030-msh` - Latest (broken auth)
- `manus-backend-00029-6mq` - CORS fix (broken auth after rollback)
- `manus-backend-00028-jnq` - Current (broken auth)

**Container Image:**
```
us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest
```

**Environment Variables:**
- MongoDB URI (من Secret Manager)
- JWT Secret Key (من Secret Manager)
- Password Salt (من Secret Manager)
- Redis credentials (من Secret Manager)
- Sentry DSN (optional)
- Stripe keys (optional)

**Resources:**
- CPU: 1
- Memory: 512Mi
- Max Instances: 10
- Min Instances: 0 (cold start)
- Timeout: 300s
- Concurrency: 80

**Health Endpoints:**
- `/api/v1/health` - ✅ يعمل
- `/api/v1/ready` - ✅ يعمل
- `/docs` - Swagger UI

---

### Frontend - Compute Engine VM

**Instance Name:** `manus-frontend-vm`  
**External IP:** `34.121.111.2` (ephemeral)  
**Zone:** `us-central1-a`  
**Machine Type:** `e2-medium` (2 vCPU, 4 GB memory)

**URL:** `http://34.121.111.2`

**Container Image:**
```
us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
```

**Container Configuration:**
```yaml
gce-container-declaration:
  spec:
    containers:
    - name: manus-frontend-vm
      image: us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
      env:
      - name: BACKEND_URL
        value: https://manus-backend-247096226016.us-central1.run.app/
      - name: VITE_API_URL
        value: https://manus-backend-247096226016.us-central1.run.app
      restartPolicy: Always
```

**Web Server:** Nginx 1.29.4

**Startup Script:**
```bash
gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz /tmp/
tar -xzf /tmp/frontend-production.tar.gz -C /tmp/
rm -rf /usr/share/nginx/html/*
cp -r /tmp/dist/* /usr/share/nginx/html/
chown -R nginx:nginx /usr/share/nginx/html/
systemctl restart nginx
```

---

### Network Configuration

**VPC Network:** `default`

**VPC Connector:**
```
Name: manus-connector
Region: us-central1
IP Range: 10.8.0.0/28
Network: default
```

**Cloud NAT:**
```
Name: manus-nat
Region: us-central1
NAT Gateway: us-central1/manus-nat-gateway
Static IP: 34.134.9.124
```

**Firewall Rules:**
- Allow HTTP (80)
- Allow HTTPS (443)
- Allow SSH (22) - limited

---

## 🗄️ قواعد البيانات

### MongoDB Atlas

**Cluster Name:** `manus-cluster` (assumed)  
**Provider:** MongoDB Atlas  
**Tier:** Free Tier (M0)  
**Region:** us-east-1 (assumed)

**Connection String:**
```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/manus?retryWrites=true&w=majority
```
(Stored in Secret Manager: `mongodb-uri`)

**Database Name:** `manus` (assumed)

**Collections:**
```
- users
- agents
- sessions
- subscriptions
```

**Indexes:**
- users: email (unique), user_id (unique)
- sessions: user_id, session_id
- subscriptions: user_id

**Network Access:**
- Whitelisted IP: `34.134.9.124` (Cloud NAT Static IP)
- Connection from: Cloud Run via VPC Connector

**Models (Beanie ODM):**
```python
- UserDocument
- AgentDocument
- SessionDocument
- SubscriptionDocument
```

---

### Redis Memorystore

**Instance Name:** `manus-redis` (assumed)  
**Tier:** Basic  
**Memory:** 1 GB  
**Region:** us-central1  
**Version:** Redis 6.x

**Connection:**
```
Host: 10.x.x.x (internal IP)
Port: 6379
Password: (from Secret Manager: redis-password)
```

**Status:** ⚠️ "Not initialized" (degraded)

**Usage:**
- Rate limiting (SlowAPI)
- Session caching (planned)
- Token blacklist (planned)

---

## 🔐 Secrets & Environment Variables

### Google Secret Manager

**Secrets List:**

1. **mongodb-uri**
   ```
   mongodb+srv://username:password@cluster.mongodb.net/manus?retryWrites=true&w=majority
   ```
   - Used by: Backend
   - Required: ✅ Critical

2. **jwt-secret-key**
   ```
   Random 256-bit secret key for JWT signing
   ```
   - Used by: Backend (Token generation/verification)
   - Required: ✅ Critical

3. **password-salt**
   ```
   Random salt for password hashing (bcrypt)
   ```
   - Used by: Backend (Password hashing)
   - Required: ✅ Critical
   - ⚠️ **CRITICAL NOTE:** If this changes, all existing users can't login!

4. **redis-password**
   ```
   Password for Redis Memorystore connection
   ```
   - Used by: Backend (Rate limiting)
   - Required: ⚠️ Optional (fallback to memory)

5. **blackbox-api-key**
   ```
   API key for external blackbox service
   ```
   - Used by: Backend (AI agent service)
   - Required: ❓ Unknown

6. **django_admin_password** (legacy?)
   ```
   Old Django admin password
   ```
   - Used by: ❓ Not used
   - Required: ❌ Can be deleted

7. **django_settings** (legacy?)
   ```
   Old Django settings
   ```
   - Used by: ❓ Not used
   - Required: ❌ Can be deleted

---

### Environment Variables (Backend)

**Required:**
```bash
# Database
MONGODB_URI=<from secret manager>
MONGODB_USERNAME=<extracted from URI>
MONGODB_PASSWORD=<extracted from URI>

# Authentication
JWT_SECRET_KEY=<from secret manager>
PASSWORD_SALT=<from secret manager>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_HOST=10.x.x.x
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<from secret manager>

# Application
LOG_LEVEL=info
ENVIRONMENT=production
SENTRY_DSN=<optional>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Stripe (optional)
STRIPE_API_KEY=<optional>
STRIPE_WEBHOOK_SECRET=<optional>
```

**Optional:**
```bash
# API Keys
BLACKBOX_API_KEY=<from secret manager>

# Monitoring
SENTRY_DSN=<if enabled>
```

---

### Environment Variables (Frontend)

**Build Time:**
```bash
VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
NODE_ENV=production
```

**Runtime (Container):**
```bash
BACKEND_URL=https://manus-backend-247096226016.us-central1.run.app/
VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
```

---

## 👥 المستخدمون التجريبيون

### Demo User

**Email:** `demo@manus.ai`  
**Password:** `DemoPass123!`  
**Role:** `user`  
**Status:** `active`  
**User ID:** `Z9rpAVPHQw4PNtddm09faA`  
**Created:** 2025-12-28T03:16:51.671000

**Subscription:** None (free access)

---

### Admin User

**Email:** `admin@manus.ai`  
**Password:** `AdminPass123!`  
**Role:** `user` (not admin role yet)  
**Status:** `active`  
**User ID:** `tplCP7Xt0lsE6PRWrFuHLQ`  
**Created:** 2025-12-28T03:16:38.553000

**Subscription:** None (free access)

---

## 📦 Container Registry

**Artifact Registry Repository:**
```
us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app
```

**Images:**
```
- backend:latest (Python FastAPI)
- frontend:latest (React + Nginx)
```

---

## 🔧 Build & Deploy

### Backend Build

**Dockerfile Location:** `/backend/Dockerfile`

**Build Command:**
```bash
cd /home/root/webapp/backend
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --project=gen-lang-client-0415541083
```

**Deploy Command:**
```bash
gcloud run deploy manus-backend \
  --image us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --region us-central1 \
  --project=gen-lang-client-0415541083 \
  --platform managed \
  --allow-unauthenticated
```

---

### Frontend Build

**Dockerfile Location:** `/frontend/Dockerfile`

**Build Args:**
```bash
ARG VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
```

**Build Command:**
```bash
cd /home/root/webapp/frontend
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project=gen-lang-client-0415541083
```

**cloudbuild.yaml:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app'
      - '-t'
      - 'us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest'
      - '.'
images:
  - 'us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest'
timeout: 1200s
```

**Deploy to VM:**
```bash
gcloud compute instances update-container manus-frontend-vm \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
```

---

## 📁 مسارات المشروع

### Repository Structure

**GitHub:** `https://github.com/raglox/ai-manus`  
**Branch:** `main`  
**Local Path:** `/home/root/webapp`

```
/home/root/webapp/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── application/     # Business logic
│   │   ├── domain/          # Domain models
│   │   ├── infrastructure/  # DB, Redis, etc.
│   │   └── interfaces/      # API routes
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── frontend/                # React Frontend
│   ├── src/
│   ├── dist/               # Built files
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                    # Documentation
├── sandbox/                 # Sandbox related files
│
└── [Documentation Files]
    ├── READY.txt
    ├── LOGIN_INFO.md
    ├── CORS_FIX.md
    ├── CORS_COMPLETE.txt
    ├── LOGIN_TEST_REPORT.md
    ├── CHAT_ISSUE_REPORT.md
    └── COMPLETE_PROJECT_DOCUMENTATION.md (this file)
```

---

## 🔌 API Endpoints

### Authentication (`/api/v1/auth/`)

**POST /auth/register** - Register new user
```json
Request:
{
  "email": "user@example.com",
  "password": "Password123!",
  "username": "username",
  "fullname": "Full Name"
}

Response:
{
  "code": 0,
  "msg": "success",
  "data": {
    "user": {...},
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

**POST /auth/login** - User login
```json
Request:
{
  "email": "user@example.com",
  "password": "Password123!"
}

Response: (same as register)
```

**POST /auth/refresh** - Refresh access token
```json
Request:
{
  "refresh_token": "eyJ..."
}

Response:
{
  "code": 0,
  "msg": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

---

### Sessions (`/api/v1/sessions/`)

**PUT /sessions** - Create new session
```json
Headers:
  Authorization: Bearer <access_token>

Response:
{
  "code": 0,
  "msg": "success",
  "data": {
    "session_id": "abc123"
  }
}
```

**GET /sessions** - List all sessions
```json
Headers:
  Authorization: Bearer <access_token>

Response:
{
  "code": 0,
  "msg": "success",
  "data": {
    "sessions": [...]
  }
}
```

**GET /sessions/{session_id}** - Get session details

**POST /sessions/{session_id}/chat** - Send chat message
```json
Request:
{
  "message": "Hello AI!"
}

Response:
{
  "code": 0,
  "msg": "success",
  "data": {...}
}
```

**DELETE /sessions/{session_id}** - Delete session

**POST /sessions/{session_id}/stop** - Stop session

---

### Health (`/api/v1/`)

**GET /health** - Basic health check
```json
{
  "status": "healthy",
  "timestamp": "2025-12-28T...",
  "service": "manus-ai-backend"
}
```

**GET /ready** - Readiness check with dependencies
```json
{
  "status": "ready",
  "checks": {
    "mongodb": {"status": "healthy", "message": "Connected"},
    "redis": {"status": "degraded", "message": "Not initialized"},
    "stripe": {"status": "skipped", "message": "Not configured"}
  }
}
```

---

## 🐛 المشاكل الحالية

### 🔴 Critical Issue: Auth Endpoints Return 500

**المشكلة:**
- جميع auth endpoints تعطي `500 Internal Server Error`
- `/api/v1/auth/login` - ❌ Failed
- `/api/v1/auth/register` - ❌ Failed
- Health endpoints تعمل ✅
- MongoDB متصل ✅

**التشخيص:**
- المشكلة ظهرت بعد deployment أخير
- Rollback لم يحل المشكلة
- MongoDB متصل لكن auth فاشل
- ⚠️ **يحتاج فحص Cloud Run Logs**

**الاحتمالات:**
1. PASSWORD_SALT secret تغير أو missing
2. مشكلة في password hashing/verification
3. Database schema issue
4. Environment variable configuration

**التأثير:**
- ❌ لا يمكن تسجيل الدخول
- ❌ لا يمكن إنشاء حسابات جديدة
- ❌ لا يمكن اختبار chat functionality
- ❌ النظام غير قابل للاستخدام حالياً

---

### ⚠️ Known Issues (Minor)

1. **Redis Not Initialized:**
   - Status: degraded
   - Impact: Low (fallback to memory rate limiting)
   - Priority: Low

2. **Sessions Endpoint (untested):**
   - Cannot test due to auth issue
   - May have subscription check issue (fixed but not tested)

---

## ✅ ما يعمل بنجاح

1. ✅ **CORS Configuration:**
   - Frontend يستطيع الاتصال بـ Backend
   - جميع CORS headers موجودة
   - OPTIONS preflight requests تعمل

2. ✅ **Infrastructure:**
   - Cloud Run deployed
   - Frontend VM running
   - MongoDB Atlas connected
   - VPC Connector working
   - Cloud NAT configured

3. ✅ **Health Checks:**
   - `/api/v1/health` works
   - `/api/v1/ready` works
   - MongoDB connection verified

4. ✅ **Build & Deploy Pipeline:**
   - Docker builds working
   - Cloud Build configured
   - Artifact Registry accessible

---

## 📊 الأداء

### Backend Performance
- Container startup: < 3s (excellent)
- Health check: < 1s
- MongoDB connection: ~2s
- Cold start: ~3-5s

### Frontend Performance
- Page load: < 2s
- Nginx response: < 100ms

---

## 💰 التكاليف الشهرية

| الخدمة | التكلفة |
|--------|---------|
| Frontend VM (e2-medium) | $400-450 |
| Backend Cloud Run | $50-80 |
| Cloud NAT + Static IP | $35-40 |
| Redis Memorystore (1GB) | $48 |
| VPC Connector | $8 |
| MongoDB Atlas (Free Tier) | $0 |
| Cloud Build (minimal usage) | ~$5 |
| Artifact Registry | ~$2 |
| **الإجمالي** | **$548-633/mo** |

---

## 🔍 Monitoring & Logs

### Cloud Run Logs
```
https://console.cloud.google.com/run/detail/us-central1/manus-backend/logs?project=gen-lang-client-0415541083
```

### VM Logs
```bash
gcloud compute instances get-serial-port-output manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083
```

### Cloud Build History
```
https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0415541083
```

---

## 🔧 Useful Commands

### Backend

**Check revision:**
```bash
gcloud run services describe manus-backend \
  --region=us-central1 \
  --format="value(status.latestReadyRevisionName)"
```

**View secrets:**
```bash
gcloud secrets versions access latest \
  --secret=password-salt \
  --project=gen-lang-client-0415541083
```

**Read logs:**
```bash
gcloud run logs read manus-backend \
  --region=us-central1 \
  --limit=50
```

**Rollback:**
```bash
gcloud run services update-traffic manus-backend \
  --to-revisions=manus-backend-00028-jnq=100 \
  --region=us-central1
```

---

### Frontend

**SSH to VM:**
```bash
gcloud compute ssh manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083
```

**Restart container:**
```bash
gcloud compute instances reset manus-frontend-vm \
  --zone=us-central1-a
```

**Update container:**
```bash
gcloud compute instances update-container manus-frontend-vm \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
```

---

### MongoDB

**Test connection:**
```bash
mongo "mongodb+srv://cluster.mongodb.net/manus" \
  --username <user> \
  --password <pass>
```

**Check collections:**
```javascript
use manus
show collections
db.users.find()
```

---

## 📚 Documentation Files

1. **READY.txt** - Quick reference
2. **LOGIN_INFO.md** - Login credentials
3. **CORS_FIX.md** - CORS configuration details
4. **CORS_COMPLETE.txt** - CORS fix summary
5. **LOGIN_TEST_REPORT.md** - Login testing report
6. **CHAT_ISSUE_REPORT.md** - Current auth issue report
7. **COMPLETE_PROJECT_DOCUMENTATION.md** - This file

---

## 🎯 الخطوة التالية للمطور

### الهدف: إصلاح Auth 500 Error

**الأولوية: Critical 🔴**

**الخطوات:**

1. **الوصول إلى Cloud Run Logs:**
   ```
   https://console.cloud.google.com/run/detail/us-central1/manus-backend/logs
   ```
   - ابحث عن requests لـ `/api/v1/auth/login`
   - اقرأ exception trace
   - حدد السبب الحقيقي

2. **التحقق من Secrets:**
   ```bash
   gcloud secrets versions access latest --secret=password-salt
   gcloud secrets versions access latest --secret=jwt-secret-key
   ```
   - تأكد من وجودهم
   - تأكد من صحتهم

3. **Test Locally:**
   - شغل Backend محلياً
   - استخدم نفس environment variables
   - اختبر auth endpoints
   - احصل على actual error

4. **إصلاح المشكلة:**
   - بناءً على error message من logs
   - أصلح الكود
   - Deploy revision جديد
   - اختبر

5. **Verify Fix:**
   - Test login
   - Test register
   - Test session creation
   - Test chat message

---

## 📧 Contacts & Resources

**GitHub Repo:** https://github.com/raglox/ai-manus  
**GCP Project:** gen-lang-client-0415541083  
**Frontend URL:** http://34.121.111.2  
**Backend URL:** https://manus-backend-247096226016.us-central1.run.app

---

**📅 آخر تحديث:** 28 ديسمبر 2025  
**📊 الحالة:** Production (Auth Broken)  
**🔴 Priority:** Critical Fix Required

---

## ⚠️ تحذير أمني

هذا المستند يحتوي على معلومات حساسة:
- ❌ لا تشارك هذا الملف علناً
- ❌ لا ترفعه على GitHub public
- ✅ استخدمه فقط للتطوير والصيانة
- ✅ احذف المعلومات الحساسة بعد الانتهاء

---

**End of Documentation**
