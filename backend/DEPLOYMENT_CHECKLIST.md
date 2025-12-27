# 🚀 قائمة متطلبات الإطلاق - Manus AI Agent

**التاريخ**: 27 ديسمبر 2025  
**الحالة الحالية**: ✅ جاهز تقنياً - يحتاج إعداد البيئة

---

## 📋 الملخص التنفيذي

### الحالة الحالية ✅
- ✅ **الكود**: 100% جاهز (282/282 اختبار ناجح)
- ✅ **الاختبارات**: كاملة ومُتحقق منها
- ✅ **Docker**: Compose files جاهزة
- ✅ **CI/CD**: GitHub Actions موجود
- ⏳ **الإعداد**: يحتاج تكوين البيئة

### الوقت المتوقع للإطلاق
- **السريع**: 2-3 ساعات (إعداد أساسي)
- **الكامل**: 4-6 ساعات (مع monitoring و security)

---

## 🎯 المتطلبات الإلزامية (Must Have)

### 1. **البيئة والاستضافة** 🖥️

#### Option A: الاستضافة السحابية (Cloud)
**الموصى به**: AWS, Google Cloud, Azure, DigitalOcean

**المتطلبات**:
```yaml
Infrastructure:
  - Compute: 
      • Backend: 2 vCPU, 4GB RAM minimum
      • MongoDB: 2GB RAM minimum
      • Redis: 1GB RAM minimum
  
  - Storage:
      • MongoDB Volume: 20GB SSD minimum
      • Logs: 10GB
  
  - Network:
      • Public IP with SSL/TLS
      • Firewall configured
      • Load Balancer (optional for HA)
```

**خيارات الاستضافة**:

| الخدمة | التكلفة الشهرية | المميزات | الموصى به |
|--------|-----------------|----------|-----------|
| **AWS ECS/EC2** | $50-100 | قابل للتوسع، managed services | ⭐⭐⭐⭐⭐ |
| **Google Cloud Run** | $30-80 | Serverless، سهل | ⭐⭐⭐⭐⭐ |
| **DigitalOcean** | $40-70 | بسيط، جيد للبداية | ⭐⭐⭐⭐ |
| **Azure Container Apps** | $50-90 | Enterprise features | ⭐⭐⭐⭐ |
| **Render.com** | $25-50 | سهل جداً، limited | ⭐⭐⭐ |

#### Option B: VPS التقليدي
- **Ubuntu 22.04 LTS** أو أحدث
- **Docker** و **Docker Compose** مثبت
- **الذاكرة**: 8GB+ RAM
- **المعالج**: 4+ cores
- **التخزين**: 50GB+ SSD

---

### 2. **المتغيرات البيئية المطلوبة** 🔐

#### **الإلزامية (Critical)**
```bash
# ====== API & LLM ======
API_KEY=sk-xxxxxxxxxxxxxx                    # DeepSeek API key ⚠️ REQUIRED
API_BASE=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# ====== Database ======
MONGODB_URI=mongodb://mongodb:27017          # Production: use MongoDB Atlas
MONGODB_DATABASE=manus_production
MONGODB_USERNAME=admin                       # ⚠️ CHANGE IN PRODUCTION
MONGODB_PASSWORD=<strong-password>           # ⚠️ GENERATE STRONG PASSWORD

# ====== Redis ======
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password>             # ⚠️ REQUIRED IN PRODUCTION

# ====== JWT Security ======
JWT_SECRET_KEY=<generate-secure-random-key>  # ⚠️ MUST CHANGE - use openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ====== Search Engine ======
SEARCH_PROVIDER=bing
BING_SEARCH_API_KEY=<your-bing-api-key>     # ⚠️ REQUIRED for search
```

#### **الموصى بها (Recommended)**
```bash
# ====== Monitoring & Logging ======
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx    # Error tracking
LOG_LEVEL=INFO                               # Production: INFO or WARNING

# ====== Email (for notifications) ======
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=<app-specific-password>
EMAIL_FROM=noreply@yourdomain.com

# ====== Stripe Billing ======
STRIPE_SECRET_KEY=sk_live_xxxxx             # Production key
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_ID_BASIC=price_xxxxx
STRIPE_PRICE_ID_PRO=price_xxxxx

# ====== CORS (Frontend URL) ======
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

#### **الاختيارية (Optional)**
```bash
# ====== Sandbox Configuration ======
SANDBOX_IMAGE=simpleyyt/manus-sandbox:latest
SANDBOX_TTL_MINUTES=30
SANDBOX_NETWORK=manus-network

# ====== Advanced Features ======
MCP_CONFIG_PATH=/etc/mcp.json
PASSWORD_HASH_ROUNDS=12                     # Higher = more secure, slower
```

---

### 3. **قاعدة البيانات (MongoDB)** 💾

#### **Option A: MongoDB Atlas (موصى به)** ⭐
**المميزات**: Managed, backups, scaling, security
**التكلفة**: Free tier (512MB) أو $9+/month

**الخطوات**:
1. إنشاء حساب في [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. إنشاء Cluster
3. إعداد Network Access (Whitelist IPs)
4. إنشاء Database User
5. الحصول على Connection String

```bash
# Example connection string
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/manus?retryWrites=true&w=majority
```

#### **Option B: Self-hosted MongoDB**
```yaml
services:
  mongodb:
    image: mongo:7.0
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PASSWORD}
    restart: unless-stopped
```

**⚠️ Important**: 
- Enable authentication in production
- Regular backups (daily minimum)
- Use separate database for production

---

### 4. **Redis Cache** 🔴

#### **Option A: Managed Redis** ⭐
- **Redis Cloud**: Free tier + paid plans
- **AWS ElastiCache**: Managed Redis
- **DigitalOcean Managed Redis**: $15+/month

#### **Option B: Self-hosted**
```yaml
services:
  redis:
    image: redis:7.0-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
```

---

### 5. **SSL/TLS Certificates** 🔒

#### **الموصى به**: Let's Encrypt (مجاني)

**خيارات التنفيذ**:

**A. Using Nginx Reverse Proxy + Certbot**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**B. Using Traefik (automatic SSL)**
```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt
```

**C. Using Cloudflare** (أسهل خيار)
- Free SSL
- DDoS protection
- CDN included

---

### 6. **Domain Name & DNS** 🌐

**المطلوب**:
- Domain name (from Namecheap, GoDaddy, Cloudflare, etc.)
- DNS configured:
  ```
  A     @              -> <your-server-ip>
  A     api            -> <your-server-ip>
  A     www            -> <your-server-ip>
  CNAME frontend       -> <frontend-url>
  ```

---

## 🔧 المتطلبات الموصى بها (Recommended)

### 7. **Monitoring & Observability** 📊

#### **Error Tracking**: Sentry
```bash
# Free tier: 5K errors/month
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Setup:
1. Create account at sentry.io
2. Create new Python project
3. Copy DSN
```

#### **Application Monitoring**: New Relic / Datadog
- Performance monitoring
- Request tracing
- Database query analytics

#### **Infrastructure Monitoring**: Prometheus + Grafana
```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

**Basic Health Checks**:
```bash
# Setup cron job to monitor
*/5 * * * * curl -f https://api.yourdomain.com/api/v1/health || alert
```

---

### 8. **Backup Strategy** 💾

#### **MongoDB Backups** (إلزامي)
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="$MONGODB_URI" --out="/backups/mongodb_$DATE"
# Upload to S3 or cloud storage
aws s3 cp /backups/mongodb_$DATE s3://your-bucket/backups/

# Retention: Keep 7 days
find /backups -type d -mtime +7 -exec rm -rf {} \;
```

#### **Automated Backup Options**:
- **MongoDB Atlas**: Automatic continuous backups
- **AWS Backup**: Automated backup service
- **Backup cron jobs**: Daily to S3/Cloud Storage

**Testing**: Test restore monthly!

---

### 9. **Logging & Log Management** 📝

#### **Centralized Logging**:

**Option A: Cloud-based** (موصى به)
- **AWS CloudWatch Logs**: Integrated with AWS
- **Google Cloud Logging**: For GCP
- **Datadog Logs**: Multi-cloud
- **Logtail**: Simple and affordable

**Option B: Self-hosted**
```yaml
# ELK Stack (Elasticsearch, Logstash, Kibana)
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    
  logstash:
    image: logstash:8.11.0
    
  kibana:
    image: kibana:8.11.0
```

**Log Configuration**:
```python
# backend/app/infrastructure/logging.py
LOG_LEVEL=INFO  # Production
LOG_FORMAT=json  # For structured logging
```

---

### 10. **CI/CD Enhancements** 🔄

#### **Current Status**: ✅ GitHub Actions exists

#### **Needed Additions**:

**A. Add Testing in CI**
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:7.0
      redis:
        image: redis:7.0
    
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ --cov
```

**B. Add Deployment Stage**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/manus
            docker-compose pull
            docker-compose up -d
```

---

## 🔐 المتطلبات الأمنية (Security)

### 11. **Security Hardening** 🛡️

#### **A. Environment Variables**
```bash
# NEVER commit to Git
# Use:
# - GitHub Secrets
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker secrets
```

#### **B. Firewall Rules**
```bash
# UFW (Ubuntu)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH (limit)
ufw enable

# Deny direct access to DB
ufw deny 27017      # MongoDB
ufw deny 6379       # Redis
```

#### **C. Rate Limiting**
Already implemented in code ✅
```python
# app/infrastructure/middleware/rate_limit.py
# - 100 requests/minute per IP
# - Redis-backed
```

#### **D. CORS Configuration**
```python
# app/main.py
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
)
```

#### **E. Database Security**
- ✅ Use authentication
- ✅ Encrypt connections (TLS)
- ✅ Principle of least privilege
- ✅ Regular security updates

---

### 12. **API Keys & Secrets** 🔑

#### **Required API Keys**:

1. **DeepSeek API Key** ⚠️ **CRITICAL**
   - Get from: https://platform.deepseek.com/
   - Cost: ~$0.14-0.28 per million tokens
   - Budget: $50-100/month for production

2. **Bing Search API Key** (if using Bing)
   - Get from: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
   - Free tier: 1000 queries/month
   - Paid: $7/1000 transactions

3. **Stripe Keys** (if using billing)
   - Get from: https://dashboard.stripe.com/
   - Test keys for staging
   - Live keys for production

4. **Sentry DSN** (error tracking)
   - Free tier available
   - Get from: https://sentry.io/

#### **Generate Secure Secrets**:
```bash
# JWT Secret (256-bit)
openssl rand -hex 32

# MongoDB Password
openssl rand -base64 32

# Redis Password
openssl rand -base64 24
```

---

## 📦 متطلبات Docker

### 13. **Docker Images** 🐳

#### **Current Status**: ✅ Dockerfiles exist

**Build Images**:
```bash
# Build all services
docker-compose build

# Or build individually
docker build -t manus-backend:latest ./backend
docker build -t manus-frontend:latest ./frontend
docker build -t manus-sandbox:latest ./sandbox
```

**Push to Registry** (for production):
```bash
# Docker Hub
docker login
docker push simpleyyt/manus-backend:latest

# Or private registry
docker tag manus-backend:latest registry.yourdomain.com/manus-backend:latest
docker push registry.yourdomain.com/manus-backend:latest
```

---

## 🚀 خطوات الإطلاق (Deployment Steps)

### Quick Start (2-3 hours)

#### **Phase 1: الإعداد الأساسي (30 min)**

1. **إعداد الخادم**
```bash
# SSH to server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y
```

2. **Clone Repository**
```bash
git clone https://github.com/yourusername/webapp.git
cd webapp
```

3. **Configure Environment**
```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env

# CRITICAL: Change these
# - API_KEY
# - MONGODB_URI (or use MongoDB Atlas)
# - JWT_SECRET_KEY
# - REDIS_PASSWORD
# - MONGODB_PASSWORD
```

#### **Phase 2: قاعدة البيانات (30 min)**

**Option A: MongoDB Atlas** (موصى به)
```bash
# 1. Create account at mongodb.com
# 2. Create cluster
# 3. Get connection string
# 4. Update .env:
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/manus
```

**Option B: Local MongoDB**
```bash
# Already in docker-compose.yml
# Just set password in .env
MONGODB_PASSWORD=$(openssl rand -base64 32)
```

#### **Phase 3: الإطلاق (30 min)**

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Test endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:5173  # Frontend
```

#### **Phase 4: SSL/Domain (30 min)**

**Using Cloudflare** (أسهل):
```bash
# 1. Add domain to Cloudflare
# 2. Update DNS:
#    A    @    -> your-server-ip
#    A    api  -> your-server-ip
# 3. Enable SSL in Cloudflare (Full mode)
# 4. Done! ✅
```

**Using Certbot**:
```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### **Phase 5: التحقق (30 min)**

```bash
# 1. Health check
curl https://api.yourdomain.com/api/v1/health

# 2. Test registration
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"fullname":"Test User","email":"test@example.com","password":"Test123!"}'

# 3. Frontend
open https://yourdomain.com

# 4. Monitor logs
docker-compose logs -f
```

---

### Production Checklist ✅

#### **قبل الإطلاق**:
- [ ] جميع environment variables مُعدّة
- [ ] API Keys صالحة ومُفعّلة
- [ ] MongoDB: authentication enabled + backups configured
- [ ] Redis: password set
- [ ] JWT_SECRET_KEY: changed from default
- [ ] SSL certificates: configured & valid
- [ ] Domain DNS: pointing to server
- [ ] Firewall: configured (only 80, 443, 22 open)
- [ ] CORS: configured for production domain
- [ ] Email: configured (if used)
- [ ] Monitoring: Sentry configured
- [ ] Backups: tested restore process
- [ ] Load testing: API can handle expected traffic

#### **بعد الإطلاق**:
- [ ] Health checks: working
- [ ] Error tracking: receiving errors
- [ ] Logs: being collected
- [ ] Backups: running daily
- [ ] SSL: auto-renewal working
- [ ] Performance: monitoring response times
- [ ] Security: run security scan
- [ ] Documentation: updated with production URLs

---

## 💰 تقدير التكاليف الشهرية

### **السيناريو A: Startup (Small Scale)**
```
Hosting (DigitalOcean Droplet 8GB):     $48
MongoDB Atlas (M10 Shared):              $9
Redis Cloud (30MB):                     Free
Domain (.com):                          $1/month
Cloudflare (Free tier):                 Free
DeepSeek API (moderate usage):          $50
Sentry (Free tier):                     Free
────────────────────────────────────
Total:                                  ~$108/month
```

### **السيناريو B: Production (Medium Scale)**
```
AWS ECS Fargate (2 tasks):              $73
MongoDB Atlas (M30 Dedicated):          $97
ElastiCache Redis (cache.t3.small):     $30
Route 53 + Certificate Manager:         $1
CloudWatch Logs:                        $10
DeepSeek API (high usage):              $150
Sentry (Team plan):                     $26
────────────────────────────────────
Total:                                  ~$387/month
```

### **السيناريو C: Enterprise (Large Scale)**
```
Kubernetes Cluster (GKE/EKS):           $200+
MongoDB Atlas (M60):                    $482
Redis Enterprise:                       $100
Load Balancer + CDN:                    $50
Advanced Monitoring (Datadog):          $75
DeepSeek API (enterprise):              $500+
Support & Backup:                       $100
────────────────────────────────────
Total:                                  ~$1,507+/month
```

---

## 📚 الموارد المفيدة

### **Documentation**:
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Compose Production](https://docs.docker.com/compose/production/)
- [MongoDB Atlas](https://docs.atlas.mongodb.com/)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

### **Tools**:
- [SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [Load Testing (k6)](https://k6.io/)
- [Uptime Monitoring (UptimeRobot)](https://uptimerobot.com/)

---

## 🎯 الخلاصة

### ✅ **جاهز الآن**:
- الكود كامل واختباراته ناجحة
- Docker Compose جاهز
- CI/CD Pipeline موجود

### ⚠️ **يحتاج إعداد**:
1. **API Keys** (DeepSeek - إلزامي)
2. **Database** (MongoDB Atlas أو self-hosted)
3. **Domain & SSL** (Cloudflare موصى به)
4. **Environment Variables** (تحديث .env)
5. **Monitoring** (Sentry - موصى به)

### ⏱️ **الوقت المتوقع**:
- **سريع**: 2-3 ساعات (إعداد أساسي)
- **كامل**: 4-6 ساعات (مع monitoring و security)

---

## 📞 الخطوة التالية

**أخبرني بما تفضل**:

1. **إطلاق سريع** 🚀
   - استخدام MongoDB Atlas
   - Cloudflare للSSL
   - DigitalOcean/AWS hosting
   - → جاهز في 2-3 ساعات

2. **إعداد Production كامل** 🏭
   - Monitoring + Logging
   - Automated backups
   - CI/CD testing
   - → 4-6 ساعات

3. **مساعدة في إعداد معين** 🔧
   - MongoDB Atlas setup
   - SSL configuration
   - Domain setup
   - API keys

**أيّ خيار تفضل؟** 😊
