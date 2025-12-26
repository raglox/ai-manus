# AI Manus - Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
cd /home/root/webapp
docker compose -f docker-compose.production.yml up -d
```

**Access:** http://172.245.232.188:5173

---

## 📍 URLs

| Service | URL |
|---------|-----|
| Frontend | http://172.245.232.188:5173 |
| Backend API | http://172.245.232.188:8002 |
| API Docs | http://172.245.232.188:8002/docs |

---

## 🔧 Essential Commands

### View Status
```bash
docker compose -f docker-compose.production.yml ps
```

### View Logs
```bash
# All services
docker compose -f docker-compose.production.yml logs -f

# Backend only
docker compose -f docker-compose.production.yml logs -f backend

# Last 50 lines
docker compose -f docker-compose.production.yml logs --tail=50 backend
```

### Restart
```bash
# All services
docker compose -f docker-compose.production.yml restart

# Single service
docker compose -f docker-compose.production.yml restart backend
```

### Stop/Start
```bash
# Stop all
docker compose -f docker-compose.production.yml down

# Start all
docker compose -f docker-compose.production.yml up -d
```

### Rebuild After Changes
```bash
docker compose -f docker-compose.production.yml build --no-cache backend
docker compose -f docker-compose.production.yml up -d
```

---

## 🔐 Security Keys

```ini
# In /home/root/webapp/.env
JWT_SECRET_KEY=4RtQtWExb41uwc7CUrzXKDRMRFXvaDnaJ51SQnnkeRw
PASSWORD_SALT=rWn5f9wnY6uW8TsXC3-ISQ
API_KEY=sk-dummy-key-for-testing
```

---

## 📊 Services

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| Frontend | webapp-frontend-1 | 5173 | ✅ Running |
| Backend | webapp-backend-1 | 8002 | ✅ Running |
| MongoDB | webapp-mongodb-1 | 27017 | ✅ Running |
| Redis | webapp-redis-1 | 6379 | ✅ Running |

---

## 🐛 Quick Troubleshooting

### Container won't start
```bash
docker compose -f docker-compose.production.yml logs <service>
docker compose -f docker-compose.production.yml up -d --force-recreate
```

### API returns 500 error
```bash
docker compose -f docker-compose.production.yml logs backend --tail=50
docker compose -f docker-compose.production.yml restart backend
```

### Port conflict
```bash
# Check what's using the port
lsof -i :8002
# Change port in docker-compose.production.yml if needed
```

---

## 🧪 Test API

### Register User
```bash
curl -X POST http://172.245.232.188:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"fullname":"Test User","email":"test@example.com","password":"Test123!"}'
```

### Login
```bash
curl -X POST http://172.245.232.188:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

---

## 📝 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (secrets) |
| `docker-compose.production.yml` | Production deployment config |
| `backend/requirements.txt` | Python dependencies |
| `FINAL_DEPLOYMENT_REPORT_ENGLISH.md` | Full documentation |

---

## 🔄 Update Procedure

```bash
# 1. Pull latest code
cd /home/root/webapp
git pull origin main

# 2. Rebuild images
docker compose -f docker-compose.production.yml build --no-cache

# 3. Restart services
docker compose -f docker-compose.production.yml up -d

# 4. Verify
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs backend --tail=20
```

---

## 🛡️ Security Checklist

- ✅ JWT secret key: 32 characters, secure
- ✅ Password salt: 16 bytes, unique
- ✅ API key: Set (replace with real key for production)
- ✅ Rate limiting: Enabled via Redis
- ✅ XSS protection: Bleach library installed
- ✅ Firewall: UFW configured for required ports

---

## 📚 Documentation

- **Full Report:** `/home/root/webapp/FINAL_DEPLOYMENT_REPORT_ENGLISH.md`
- **Arabic Guide:** `/home/root/webapp/DEPLOYMENT_SUMMARY.md`
- **API Docs:** http://172.245.232.188:8002/docs
- **GitHub:** https://github.com/simpleyyt/ai-manus

---

## 🆘 Emergency Contacts

- **QQ Group:** 1005477581
- **Demo Site:** https://app.ai-manus.com
- **Documentation:** https://docs.ai-manus.com

---

**Version:** 1.0  
**Last Updated:** December 26, 2025  
**Deployment Status:** ✅ Fully Operational
