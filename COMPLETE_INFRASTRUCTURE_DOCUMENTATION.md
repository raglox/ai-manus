# 🏗️ وثيقة البنية التحتية الكاملة لمشروع Manus AI
# Complete Infrastructure & System Documentation

---

## 📋 جدول المحتويات / Table of Contents

1. [معلومات المشروع العامة](#project-overview)
2. [البنية التحتية](#infrastructure)
3. [الخوادم والخدمات](#servers-services)
4. [قواعد البيانات](#databases)
5. [الأسرار والمفاتيح](#secrets-credentials)
6. [التطبيق الأمامي (Frontend)](#frontend)
7. [التطبيق الخلفي (Backend)](#backend)
8. [الشبكات والاتصالات](#networking)
9. [المشكلة الحالية](#current-issue)
10. [برومبت للمبرمج التالي](#developer-prompt)

---

<a name="project-overview"></a>
## 1. 📊 معلومات المشروع العامة / Project Overview

### Project Name
**Manus AI** - AI-powered Agent Management System

### Project Status
- **Version:** 1.0.2
- **Status:** 🟡 PARTIALLY WORKING
  - ✅ Infrastructure: DEPLOYED
  - ✅ MongoDB: CONNECTED
  - ✅ Frontend: WORKING
  - ✅ Health Endpoints: WORKING
  - ⚠️ CORS: FIXED (was broken, now working)
  - ❌ Auth Endpoints: **BROKEN** (returning 500 errors)

### Repository
- **GitHub:** https://github.com/raglox/ai-manus
- **Branch:** main (also has: genspark_ai_developer)

### Last Updated
**28 ديسمبر 2025** / **December 28, 2025**

---

<a name="infrastructure"></a>
## 2. 🏗️ البنية التحتية / Infrastructure

### Google Cloud Project
```
Project ID: gen-lang-client-0415541083
Project Number: 247096226016
Region: us-central1
Zone: us-central1-a
```

### Infrastructure Components

#### 1. Cloud Run Service (Backend)
```yaml
Service Name: manus-backend
URL: https://manus-backend-247096226016.us-central1.run.app
Region: us-central1
Current Revision: manus-backend-00028-jnq (after rollback)
Previous Revisions:
  - manus-backend-00030-msh (broken - auth 500 error)
  - manus-backend-00029-6mq (broken - auth 500 error)
  - manus-backend-00028-jnq (current - also broken)

Container Image: us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest

Resources:
  CPU: 2 cores
  Memory: 4 GiB
  
Startup Probe:
  Type: TCP Socket
  Port: 8000
  Timeout: 240s
  Period: 240s
  Failure Threshold: 1

Service Account: 247096226016-compute@developer.gserviceaccount.com
```

#### 2. Compute Engine VM (Frontend)
```yaml
Instance Name: Manus-frontend-vm
Zone: us-central1-a
Machine Type: n1-standard-4 (estimated)
External IP: 34.121.111.2 (ephemeral)
Internal IP: 10.x.x.x (VPC)

Container:
  Image: us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
  Environment:
    VITE_API_URL: https://manus-backend-247096226016.us-central1.run.app
    
Web Server: Nginx 1.29.4
Startup Script: 
  - Copies frontend-production.tar.gz from gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/
  - Extracts to /usr/share/nginx/html
  - Restarts nginx
```

#### 3. Cloud NAT
```yaml
Name: manus-nat (assumed)
Region: us-central1
Static IP: 34.134.9.124
VPC Connector: manus-connector

Purpose: Allows Cloud Run to connect to MongoDB Atlas
```

#### 4. VPC Connector
```yaml
Name: manus-connector
Region: us-central1
IP Range: 10.x.x.x/28 (exact range not documented)

Connected Services:
  - manus-backend (Cloud Run)
  
Purpose: Enables serverless-to-VPC communication
```

#### 5. Artifact Registry
```yaml
Repository: manus-app
Region: us-central1
Format: Docker

Images:
  - backend:latest (Python FastAPI application)
  - frontend:latest (React + Nginx)
```

#### 6. Cloud Storage
```yaml
Bucket: gen-lang-client-0415541083_cloudbuild
Region: us-central1

Key Paths:
  - source/ (Cloud Build tarballs)
  - frontend-deployment/frontend-production.tar.gz
  - frontend-deployment/fix-frontend.sh
```

#### 7. Secrets Manager
```yaml
Secrets Count: 7
Secrets:
  1. blackbox-api-key
  2. django_admin_password (legacy?)
  3. django_settings (legacy?)
  4. jwt-secret-key
  5. mongodb-uri
  6. password-salt
  7. redis-password
```

---

<a name="servers-services"></a>
## 3. 🖥️ الخوادم والخدمات / Servers & Services

### Backend Service (Cloud Run)

#### Service URL
```
https://manus-backend-247096226016.us-central1.run.app
```

#### API Endpoints

**Health & Status:**
```bash
# Health Check (✅ WORKING)
GET /api/v1/health
Response: {"status":"healthy","timestamp":"2025-12-28T05:27:04.519832+00:00","service":"manus-ai-backend"}

# Readiness Check (✅ WORKING)
GET /api/v1/ready
Response: {
  "status": "ready",
  "checks": {
    "mongodb": {"status": "healthy", "message": "Connected"},
    "redis": {"status": "degraded", "message": "Not initialized"},
    "stripe": {"status": "skipped", "message": "Not configured"}
  }
}

# API Documentation (✅ WORKING)
GET /docs
Interactive Swagger UI with all endpoints
```

**Authentication (❌ BROKEN - 500 Error):**
```bash
# Login (❌ BROKEN)
POST /api/v1/auth/login
Body: {"email": "demo@manus.ai", "password": "DemoPass123!"}
Expected: JWT tokens
Actual: {"code": 500, "msg": "Internal server error", "data": null}

# Register (❌ BROKEN)
POST /api/v1/auth/register
Body: {"email": "...", "password": "...", "username": "...", "fullname": "..."}
Expected: User created + JWT tokens
Actual: {"code": 500, "msg": "Internal server error", "data": null}

# Refresh Token (❓ UNKNOWN)
POST /api/v1/auth/refresh
Expected: New access token
Status: Untested (can't get initial tokens)
```

**Sessions (❓ UNKNOWN - Can't test without auth):**
```bash
# Create Session
PUT /api/v1/sessions
Headers: Authorization: Bearer <token>
Expected: New session_id
Status: Untested

# Get Session
GET /api/v1/sessions/{session_id}
Expected: Session details
Status: Untested

# Delete Session
DELETE /api/v1/sessions/{session_id}
Expected: Session deleted
Status: Untested
```

**Billing (❓ UNKNOWN):**
```bash
# Get Subscription
GET /api/v1/billing/subscription

# Create Portal Session
POST /api/v1/billing/portal-session

# Stripe Webhook
POST /api/v1/billing/webhook
```

#### Environment Variables (Cloud Run)
```yaml
LLM_PROVIDER: blackbox
LOG_LEVEL: INFO
MONGODB_DATABASE: manus
REDIS_HOST: 10.236.19.107
REDIS_PORT: 6379

# From Secrets:
MONGODB_URI: (from secret: mongodb-uri)
JWT_SECRET_KEY: (from secret: jwt-secret-key)
PASSWORD_SALT: (from secret: password-salt)
BLACKBOX_API_KEY: (from secret: blackbox-api-key)
REDIS_PASSWORD: (from secret: redis-password)
```

### Frontend Service (VM + Nginx)

#### Access URL
```
http://34.121.111.2
```

#### Configuration
```yaml
Web Server: Nginx 1.29.4
Document Root: /usr/share/nginx/html
Port: 80 (HTTP)

Build Configuration:
  Tool: Vite
  Build Arg: VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
  
JavaScript Bundle:
  - Contains hardcoded API URL (extracted via curl)
  - All API calls go to: https://manus-backend-247096226016.us-central1.run.app
  - CORS origin: http://34.121.111.2
```

#### Files & Paths
```bash
Container Image: 
  us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest

Deployment Archive:
  gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz

Local Build Output:
  /home/root/webapp/frontend/dist/
```

---

<a name="databases"></a>
## 4. 🗄️ قواعد البيانات / Databases

### MongoDB Atlas

#### Connection Details
```yaml
Provider: MongoDB Atlas (Cloud)
Cluster: Cluster0.9h9x33.mongodb.net
Database: manus

Connection String:
  mongodb+srv://jadjadhos5_db_user:05vYi9XJkEPLGTHF@cluster0.9h9x33.mongodb.net/manus?retryWrites=true&w=majority

Connection Method: Beanie ODM (async)
Status: ✅ CONNECTED (verified via /api/v1/ready)
```

#### Collections (via Beanie)
```python
1. users
   - Schema: User model
   - Fields: id, fullname, email, password_hash, role, is_active, created_at, updated_at, last_login_at
   - Indexes: email (unique)

2. agents
   - Schema: Agent model
   - Purpose: AI agent configurations

3. sessions
   - Schema: Session model
   - Purpose: User chat sessions

4. subscriptions
   - Schema: Subscription model
   - Purpose: Billing and usage tracking
```

#### Test Users (Pre-created)
```yaml
User 1 (Demo):
  ID: Z9rpAVPHQw4PNtddm09faA
  Email: demo@manus.ai
  Password: DemoPass123!
  Fullname: Demo User
  Role: user
  Status: active
  Created: 2025-12-28T03:16:51.671000
  ⚠️ Note: Login currently failing with 500 error

User 2 (Admin):
  ID: tplCP7Xt0lsE6PRWrFuHLQ
  Email: admin@manus.ai
  Password: AdminPass123!
  Fullname: Admin User
  Role: user (not admin!)
  Status: active
  Created: 2025-12-28T03:16:38.553000
  ⚠️ Note: Login currently failing with 500 error
```

#### Initialization
```python
# Backend: Lazy DB initialization
# Path: backend/app/infrastructure/database/db.py

async def init_beanie():
    """Initialize Beanie ODM with MongoDB"""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client[settings.MONGODB_DATABASE]
    
    await init_beanie(
        database=database,
        document_models=[
            User,
            Agent,
            Session,
            Subscription
        ]
    )
```

### Redis (Memorystore)

#### Connection Details
```yaml
Host: 10.236.19.107 (VPC internal)
Port: 6379
Password: (from secret: redis-password)
Database: 0

Status: ⚠️ DEGRADED (Not initialized)
Purpose: Rate limiting & caching
Fallback: In-memory rate limiter
```

#### Current State
```
Redis is configured but not connecting:
- /api/v1/ready shows: "redis": {"status": "degraded", "message": "Not initialized"}
- System falls back to SlowAPI in-memory rate limiter
- Not critical for basic functionality
```

---

<a name="secrets-credentials"></a>
## 5. 🔐 الأسرار والمفاتيح / Secrets & Credentials

### ⚠️ CRITICAL SECURITY NOTICE
**هذه معلومات حساسة للغاية - يجب الحفاظ على سريتها**
**These are HIGHLY SENSITIVE - Must be kept confidential**

### Google Cloud Secrets Manager

#### Secret: mongodb-uri
```
mongodb+srv://jadjadhos5_db_user:05vYi9XJkEPLGTHF@cluster0.9h9x33.mongodb.net/manus?retryWrites=true&w=majority

Username: jadjadhos5_db_user
Password: 05vYi9XJkEPLGTHF
Cluster: cluster0.9h9x33.mongodb.net
Database: manus
```

#### Secret: jwt-secret-key
```
7fa259ac28c4779014373b83cba325178098a725e36d5cd1cddeb7a4bfe8a0c5
```

#### Secret: password-salt
```
_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c
```

#### Secret: blackbox-api-key
```
sk-SuSCd8TN7baNnh2EcFnGzw
```

#### Secret: redis-password
```
(Value not extracted - access via gcloud CLI if needed)
```

#### Secret: django_admin_password
```
(Legacy secret - may not be used)
```

#### Secret: django_settings
```
(Legacy secret - may not be used)
```

### Test User Credentials

#### Demo User
```
Email: demo@manus.ai
Password: DemoPass123!
Role: user
```

#### Admin User
```
Email: admin@manus.ai
Password: AdminPass123!
Role: user
```

### Password Hashing Configuration
```python
# Algorithm: PBKDF2 SHA256
# Salt: _CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c
# Rounds: 10 (or configured value)

# Password verification happens in:
# backend/app/domain/services/auth_service.py
```

---

<a name="frontend"></a>
## 6. 🎨 التطبيق الأمامي / Frontend

### Technology Stack
```yaml
Framework: React 18.x
Build Tool: Vite
Language: TypeScript
UI Components: Custom + TailwindCSS (assumed)
HTTP Client: Fetch API / Axios
```

### Build Configuration

#### Dockerfile
```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Cloud Build Configuration
```yaml
# File: frontend/cloudbuild.yaml
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

### Deployment Status
```yaml
Status: ✅ DEPLOYED & WORKING

URL: http://34.121.111.2
API URL (hardcoded in build): https://manus-backend-247096226016.us-central1.run.app

Last Build: December 28, 2025
Image: us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest

Verification:
  - Frontend loads: ✅ YES (200 OK)
  - API URL correct: ✅ YES (verified via bundle inspection)
  - CORS configured: ✅ YES (backend allows http://34.121.111.2)
  - Login page accessible: ✅ YES
  - Login functionality: ❌ NO (backend returns 500)
```

### File Structure
```
/home/root/webapp/frontend/
├── dist/                    # Build output
│   ├── index.html
│   ├── assets/
│   │   ├── index-{hash}.js
│   │   └── index-{hash}.css
│   └── ...
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/           # API calls
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── Dockerfile
└── cloudbuild.yaml
```

---

<a name="backend"></a>
## 7. ⚙️ التطبيق الخلفي / Backend

### Technology Stack
```yaml
Framework: FastAPI 0.x
Language: Python 3.11+
ODM: Beanie (MongoDB async)
Auth: JWT (PyJWT)
Rate Limiting: SlowAPI
CORS: FastAPI CORSMiddleware + Custom Middleware
API Docs: Swagger UI (FastAPI built-in)
```

### Project Structure
```
/home/root/webapp/backend/
├── app/
│   ├── main.py                           # FastAPI app entry point
│   ├── domain/
│   │   ├── models/                       # Beanie document models
│   │   │   ├── user.py
│   │   │   ├── agent.py
│   │   │   ├── session.py
│   │   │   └── subscription.py
│   │   ├── services/                     # Business logic
│   │   │   ├── auth_service.py          # ⚠️ Auth logic (broken)
│   │   │   ├── agent_service.py
│   │   │   └── subscription_service.py
│   │   └── repositories/                 # Data access
│   │       ├── user_repository.py
│   │       └── subscription_repository.py
│   ├── interfaces/
│   │   ├── api/                          # API routes
│   │   │   ├── auth_routes.py           # ⚠️ Login/Register (500 error)
│   │   │   ├── session_routes.py
│   │   │   ├── billing_routes.py
│   │   │   └── health_routes.py         # ✅ Working
│   │   ├── errors/
│   │   │   ├── exception_handlers.py    # Custom exception handlers
│   │   │   └── exceptions.py            # Custom exception classes
│   │   └── schemas/                      # Pydantic models
│   │       ├── user_schema.py
│   │       ├── auth_schema.py
│   │       └── ...
│   └── infrastructure/
│       ├── database/
│       │   └── db.py                     # MongoDB/Beanie init
│       ├── middleware/
│       │   ├── cors_handler.py          # Custom CORS middleware
│       │   ├── rate_limiter.py
│       │   └── __init__.py
│       └── config/
│           └── (settings files - if any)
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Key Code Sections

#### main.py - Application Setup
```python
from fastapi import FastAPI
from app.infrastructure.middleware.cors_handler import CORSHeaderMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Create app
app = FastAPI(
    title="Manus AI Agent",
    lifespan=lifespan  # Lazy DB init
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# CORS Middleware
app.add_middleware(
    CORSHeaderMiddleware,
    allowed_origins=[
        "http://34.121.111.2",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Exception handlers (with CORS)
from app.interfaces.errors.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    general_exception_handler
)
```

#### auth_service.py - Authentication Logic (⚠️ SUSPECTED ISSUE)
```python
# File: app/domain/services/auth_service.py

class AuthService:
    async def login_with_tokens(self, email: str, password: str):
        """
        ⚠️ THIS METHOD IS RETURNING 500 ERROR
        
        Expected flow:
        1. Find user by email
        2. Verify password hash (using PASSWORD_SALT)
        3. Generate JWT tokens
        4. Return user + tokens
        
        Current issue:
        - All steps failing with 500 error
        - No logs accessible to debug
        - Password verification may be failing
        - JWT generation may be failing
        """
        # ... implementation ...
```

#### exception_handlers.py - Error Handling with CORS
```python
# File: app/interfaces/errors/exception_handlers.py

def _add_cors_headers(response: Response) -> Response:
    """Add CORS headers to exception responses"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom app exceptions with CORS"""
    response = JSONResponse(...)
    return _add_cors_headers(response)
```

### Environment Variables & Configuration
```python
# Required environment variables (from Cloud Run config):

LLM_PROVIDER=blackbox
LOG_LEVEL=INFO
MONGODB_DATABASE=manus
REDIS_HOST=10.236.19.107
REDIS_PORT=6379

# From secrets:
MONGODB_URI=(secret)
JWT_SECRET_KEY=(secret)
PASSWORD_SALT=(secret)
BLACKBOX_API_KEY=(secret)
REDIS_PASSWORD=(secret)
```

### Deployment Process
```bash
# 1. Build Docker image
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --project=gen-lang-client-0415541083 \
  backend/

# 2. Deploy to Cloud Run
gcloud run deploy manus-backend \
  --image us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "LLM_PROVIDER=blackbox,LOG_LEVEL=INFO,..." \
  --set-secrets "MONGODB_URI=mongodb-uri:latest,JWT_SECRET_KEY=jwt-secret-key:latest,..."
```

---

<a name="networking"></a>
## 8. 🌐 الشبكات والاتصالات / Networking

### Network Flow

```
User Browser (http://34.121.111.2)
    ↓
Frontend VM (Nginx)
    ↓
Backend Cloud Run (https://manus-backend-247096226016.us-central1.run.app)
    ↓
VPC Connector (manus-connector)
    ↓
Cloud NAT (34.134.9.124)
    ↓
MongoDB Atlas (cluster0.9h9x33.mongodb.net)

Redis Memorystore (10.236.19.107:6379) ← Not connecting
```

### CORS Configuration

#### Frontend → Backend
```yaml
Frontend Origin: http://34.121.111.2
Backend CORS Policy:
  - Allowed Origins:
      - http://34.121.111.2 ✅
      - http://localhost:5173 ✅
      - http://localhost:3000 ✅
  - Allow Credentials: true
  - Allowed Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
  - Allowed Headers: * (all)
  - Exposed Headers: * (all)
  - Max Age: 3600 seconds

Status: ✅ WORKING (fixed via CORSHeaderMiddleware)
```

#### Preflight Requests
```bash
# OPTIONS request test
curl -X OPTIONS "https://manus-backend-247096226016.us-central1.run.app/api/v1/sessions" \
  -H "Origin: http://34.121.111.2" \
  -H "Access-Control-Request-Method: POST"

# Result: ✅ 200 OK with correct CORS headers
```

### IP Addresses & URLs

#### Public IPs
```
Frontend VM: 34.121.111.2 (ephemeral)
Cloud NAT: 34.134.9.124 (static)
```

#### Service URLs
```
Frontend: http://34.121.111.2
Backend: https://manus-backend-247096226016.us-central1.run.app
API Docs: https://manus-backend-247096226016.us-central1.run.app/docs
Health: https://manus-backend-247096226016.us-central1.run.app/api/v1/health
Ready: https://manus-backend-247096226016.us-central1.run.app/api/v1/ready
```

#### Internal IPs
```
Redis: 10.236.19.107:6379
VPC Connector: 10.x.x.x/28 (exact range not documented)
```

---

<a name="current-issue"></a>
## 9. 🐛 المشكلة الحالية / Current Issue

### Issue Summary
**All authentication endpoints are returning HTTP 500 Internal Server Error**

### Affected Endpoints
```bash
❌ POST /api/v1/auth/login       → 500 error
❌ POST /api/v1/auth/register    → 500 error
❌ POST /api/v1/auth/refresh     → Untested (can't get initial token)
```

### What Works
```bash
✅ GET /api/v1/health            → 200 OK
✅ GET /api/v1/ready             → 200 OK (shows MongoDB connected)
✅ GET /docs                     → 200 OK (Swagger UI loads)
✅ CORS headers                  → Present on all responses
✅ OPTIONS preflight requests    → 200 OK with correct headers
✅ Frontend loads                → 200 OK
✅ MongoDB connection            → Connected (verified)
```

### What Doesn't Work
```bash
❌ User login (demo@manus.ai)    → 500 error
❌ User login (admin@manus.ai)   → 500 error  
❌ New user registration         → 500 error
❌ Session creation              → Can't test (needs auth)
❌ Chat functionality            → Can't test (needs session)
```

### Error Response
```json
{
  "code": 500,
  "msg": "Internal server error",
  "data": null
}
```

### Timeline
```
1. ✅ Initial deployment working (revisions 00028, 00029)
2. 🔧 Added session subscription check (revision 00030)
3. ❌ Auth endpoints started failing (500 error)
4. 🔄 Rolled back to 00029 → Still broken
5. 🔄 Rolled back to 00028 → Still broken
6. 🤔 Conclusion: Issue is NOT in code changes
```

### Hypotheses

#### Hypothesis 1: Password Hash Mismatch
```
Possibility: Password salt or hashing algorithm changed/misconfigured
Evidence:
  - Both demo and admin users fail login
  - Register also fails (should work for new users)
  - MongoDB is connected (rules out DB issue)
  
Likelihood: Medium
```

#### Hypothesis 2: JWT Secret Issue
```
Possibility: JWT secret key not properly loaded or corrupted
Evidence:
  - All auth endpoints fail
  - Health check works (doesn't use JWT)
  
Likelihood: Medium
```

#### Hypothesis 3: Environment Variable Missing
```
Possibility: Critical env var not passed to container
Evidence:
  - Rollback didn't fix (suggests config issue)
  - Ready check shows services healthy
  
Likelihood: Low (all secrets configured)
```

#### Hypothesis 4: Database Schema Mismatch
```
Possibility: User model schema changed but DB data is old format
Evidence:
  - MongoDB connected
  - Can't verify without logs
  
Likelihood: Low
```

#### Hypothesis 5: Python Exception in Auth Code
```
Possibility: Unhandled exception in auth_service.py
Evidence:
  - Generic 500 error
  - Exception handler catches and returns 500
  - No stack trace accessible
  
Likelihood: HIGH (most probable)
```

### What's Needed
```
🚨 CRITICAL: Access to Cloud Run logs to see actual exception trace

Without logs, we are debugging blind!

How to access logs:
1. GCP Console: https://console.cloud.google.com/run/detail/us-central1/manus-backend/logs
2. gcloud CLI: gcloud run logs read manus-backend --region=us-central1 --limit=50
3. Alternative: Add debug endpoint that catches and returns exception details
```

### Attempted Fixes
```
✅ Fixed CORS issues (was successful)
✅ Added exception handler CORS headers (successful)
✅ Added try/except to session subscription check (deployed as 00030)
❌ Rollback to 00029 (didn't help)
❌ Rollback to 00028 (didn't help)
```

---

<a name="developer-prompt"></a>
## 10. 👨‍💻 برومبت للمبرمج التالي / Developer Prompt

# 🎯 Prompt for Next Developer

## Context
You are taking over the **Manus AI** project, which is an AI-powered agent management system deployed on Google Cloud Platform. The system consists of:
- **Frontend:** React + Vite + Nginx on Compute Engine VM
- **Backend:** FastAPI + MongoDB + Redis on Cloud Run
- **Database:** MongoDB Atlas (cloud-hosted)

## Current Status

### ✅ What's Working
1. Infrastructure is fully deployed
2. Frontend loads and displays correctly
3. Backend health endpoints respond (GET /api/v1/health, GET /api/v1/ready)
4. MongoDB is connected and accessible
5. CORS is properly configured
6. API documentation is accessible at /docs

### ❌ Critical Issue
**All authentication endpoints are returning HTTP 500 errors:**
- `POST /api/v1/auth/login` → 500 error
- `POST /api/v1/auth/register` → 500 error

This blocks all user functionality including:
- User login
- New user registration
- Session creation
- Chat functionality

## System Access

### URLs
```
Frontend:  http://34.121.111.2
Backend:   https://manus-backend-247096226016.us-central1.run.app
API Docs:  https://manus-backend-247096226016.us-central1.run.app/docs
GitHub:    https://github.com/raglox/ai-manus
```

### Google Cloud Project
```
Project ID: gen-lang-client-0415541083
Project Number: 247096226016
Region: us-central1
```

### Test Credentials
```
Demo User:
  Email: demo@manus.ai
  Password: DemoPass123!
  
Admin User:
  Email: admin@manus.ai
  Password: AdminPass123!
```

### Secrets (Google Cloud Secrets Manager)
```
- mongodb-uri: mongodb+srv://jadjadhos5_db_user:05vYi9XJkEPLGTHF@cluster0.9h9x33.mongodb.net/manus?retryWrites=true&w=majority
- jwt-secret-key: 7fa259ac28c4779014373b83cba325178098a725e36d5cd1cddeb7a4bfe8a0c5
- password-salt: _CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c
- blackbox-api-key: sk-SuSCd8TN7baNnh2EcFnGzw
- redis-password: (access via gcloud CLI if needed)
```

## Your Task

### Primary Objective
**Fix the authentication endpoints so users can log in and register.**

### Investigation Steps

#### Step 1: Access Cloud Run Logs
```bash
# View recent logs
gcloud run logs read manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083 \
  --limit=50

# Filter for error logs
gcloud run logs read manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083 \
  --limit=100 | grep -i "error\|exception\|traceback"
```

**Or use GCP Console:**
https://console.cloud.google.com/run/detail/us-central1/manus-backend/logs

**Look for:**
- Python exception traces
- Stack traces pointing to specific files/lines
- Error messages related to password, JWT, or database

#### Step 2: Test Auth Endpoints Manually
```bash
# Test login
curl -X POST "https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@manus.ai","password":"DemoPass123!"}'

# Test register
curl -X POST "https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"TestPass123!","username":"testuser","fullname":"Test User"}'
```

#### Step 3: Check Code Paths
Based on logs, examine these files:
```
backend/app/domain/services/auth_service.py        # Login/register logic
backend/app/interfaces/api/auth_routes.py           # API endpoints
backend/app/domain/models/user.py                   # User model
backend/app/infrastructure/database/db.py           # Database init
backend/app/interfaces/errors/exception_handlers.py # Error handling
```

#### Step 4: Verify Environment Variables
```bash
# Check Cloud Run service config
gcloud run services describe manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083 \
  --format="yaml"

# Verify secrets are mounted
gcloud run services describe manus-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### Likely Root Causes

#### 1. Password Verification Issue
```python
# File: backend/app/domain/services/auth_service.py

# Likely issue:
# - PASSWORD_SALT not loaded correctly
# - Password hashing algorithm mismatch
# - User password_hash in DB doesn't match verification logic

# Check:
async def login_with_tokens(self, email: str, password: str):
    user = await self.user_repo.find_by_email(email)
    # ⚠️ This line might be throwing exception:
    is_valid = await self._verify_password(password, user.password_hash)
```

#### 2. JWT Token Generation Issue
```python
# File: backend/app/domain/services/auth_service.py or jwt utilities

# Likely issue:
# - JWT_SECRET_KEY not loaded
# - JWT library import error
# - Token encoding failing

# Check:
def create_access_token(self, user_id: str):
    # ⚠️ This might be throwing exception:
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
```

#### 3. Database Query Issue
```python
# File: backend/app/domain/repositories/user_repository.py

# Likely issue:
# - User schema mismatch
# - Beanie query failing
# - Field type mismatch

# Check:
async def find_by_email(self, email: str) -> User:
    # ⚠️ This might be throwing exception:
    user = await User.find_one(User.email == email)
```

### Debugging Strategy

#### Add Debug Logging
```python
# Temporarily add verbose logging to auth_service.py

import logging
logger = logging.getLogger(__name__)

async def login_with_tokens(self, email: str, password: str):
    try:
        logger.info(f"Login attempt for email: {email}")
        
        user = await self.user_repo.find_by_email(email)
        logger.info(f"User found: {user.id if user else 'None'}")
        
        is_valid = await self._verify_password(password, user.password_hash)
        logger.info(f"Password valid: {is_valid}")
        
        access_token = self._create_access_token(user.id)
        logger.info(f"Access token created")
        
        return LoginResponse(...)
    except Exception as e:
        logger.error(f"Login failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
```

#### Test Password Hashing
```python
# Create test script to verify password hashing works

from app.domain.services.auth_service import AuthService
import asyncio

async def test_password():
    # Test password hashing
    salt = "_CTzUJ8IDG1RZBHCF3dtq6sREcCnmSMyy169m-DAi8c"
    password = "DemoPass123!"
    
    # Hash password
    hashed = hash_password(password, salt)
    print(f"Hashed: {hashed}")
    
    # Verify password
    is_valid = verify_password(password, hashed, salt)
    print(f"Valid: {is_valid}")

asyncio.run(test_password())
```

#### Test MongoDB Connection
```python
# Verify MongoDB and Beanie are working

from app.infrastructure.database.db import init_beanie
from app.domain.models.user import User
import asyncio

async def test_db():
    await init_beanie()
    
    # Find demo user
    user = await User.find_one(User.email == "demo@manus.ai")
    print(f"User found: {user.fullname if user else 'None'}")
    print(f"Password hash: {user.password_hash[:50]}..." if user else "N/A")

asyncio.run(test_db())
```

### Fix & Deploy Process

#### 1. Make Code Changes
```bash
cd /home/root/webapp/backend

# Edit files as needed
# Example: backend/app/domain/services/auth_service.py
```

#### 2. Test Locally (if possible)
```bash
cd backend
python -m uvicorn app.main:app --reload
```

#### 3. Commit Changes
```bash
git add .
git commit -m "fix(auth): Fix authentication endpoint 500 error - [describe fix]"
git push origin main
```

#### 4. Build & Deploy
```bash
# Build new image
cd backend
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --project=gen-lang-client-0415541083

# Deploy to Cloud Run
gcloud run deploy manus-backend \
  --image us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

#### 5. Test After Deployment
```bash
# Wait 30 seconds for deployment
sleep 30

# Test login
curl -X POST "https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@manus.ai","password":"DemoPass123!"}'

# Expected: HTTP 200 with tokens (not 500)
```

### Success Criteria

Your fix is complete when:
- ✅ `POST /api/v1/auth/login` returns 200 with access token
- ✅ `POST /api/v1/auth/register` returns 200 with new user data
- ✅ Demo user can log in via frontend (http://34.121.111.2)
- ✅ New users can register via frontend
- ✅ Users can create sessions after login
- ✅ All CORS headers remain intact

### Resources

#### Documentation Files
```
/home/root/webapp/
├── CHAT_ISSUE_REPORT.md              # Current issue details
├── CORS_COMPLETE.txt                 # CORS fix documentation
├── READY.txt                         # System status
├── LOGIN_INFO.md                     # Login credentials
├── COMPLETE_PROJECT_DOCUMENTATION.md # Full technical docs
└── COMPLETE_INFRASTRUCTURE_DOCUMENTATION.md  # This file
```

#### Code Locations
```
/home/root/webapp/backend/app/
├── main.py                              # FastAPI app entry
├── domain/services/auth_service.py      # Auth logic ⚠️
├── interfaces/api/auth_routes.py        # Auth endpoints ⚠️
├── domain/models/user.py                # User model
└── infrastructure/database/db.py        # DB initialization
```

#### Useful Commands
```bash
# View logs
gcloud run logs read manus-backend --region=us-central1 --limit=50

# Describe service
gcloud run services describe manus-backend --region=us-central1

# List secrets
gcloud secrets list --project=gen-lang-client-0415541083

# Access secret
gcloud secrets versions access latest --secret="mongodb-uri"

# List revisions
gcloud run revisions list --service=manus-backend --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic manus-backend \
  --region=us-central1 \
  --to-revisions=manus-backend-00029-6mq=100
```

### Contact & Escalation

If you need additional information:
1. Check GitHub repository: https://github.com/raglox/ai-manus
2. Review commit history for recent changes
3. Check Cloud Run logs for exception traces
4. Review this documentation for context

### Good Luck! 🚀

Remember: The logs are your friend. Start with `gcloud run logs read` to see the actual exception, then work backward from there.

---

## 📝 نهاية الوثيقة / End of Document

**آخر تحديث / Last Updated:** 28 ديسمبر 2025 / December 28, 2025  
**الإصدار / Version:** 1.0.0  
**الحالة / Status:** 🟡 CRITICAL ISSUE - Auth Endpoints Broken  

---

## 📞 للدعم الفني / For Technical Support

**GitHub:** https://github.com/raglox/ai-manus  
**Documentation:** /home/root/webapp/  

---

**🔐 CONFIDENTIAL - Contains sensitive credentials and infrastructure details**
**⚠️ Do not share publicly - For authorized personnel only**

