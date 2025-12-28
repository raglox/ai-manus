# 🎯 Manus AI - معلومات الدخول والاختبار
**تاريخ:** 2025-12-28 | **الحالة:** ✅ جاهز

---

## 🌐 روابط الوصول الأساسية

### Frontend (الواجهة)
**URL:** http://34.121.111.2  
**الحالة:** ✅ يعمل

### Backend API
**URL:** https://manus-backend-247096226016.us-central1.run.app  
**الحالة:** ✅ يعمل  
**Swagger UI:** https://manus-backend-247096226016.us-central1.run.app/docs

---

## ⚡ أسرع طريقة للاختبار

### افتح Swagger UI (واجهة تفاعلية):
```
https://manus-backend-247096226016.us-central1.run.app/docs
```

### أو اختبر عبر API مباشرة:
```bash
# Health Check
curl https://manus-backend-247096226016.us-central1.run.app/api/v1/health

# Ready Check (MongoDB + Redis status)
curl https://manus-backend-247096226016.us-central1.run.app/api/v1/ready
```

---

## 📋 إعداد نهائي مطلوب (25 دقيقة)

### 1. إضافة PASSWORD_SALT (10 دقيقة)
```bash
# توليد salt
PASSWORD_SALT=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# إنشاء secret
echo -n "$PASSWORD_SALT" | gcloud secrets create password-salt \
  --data-file=- --project=gen-lang-client-0415541083

# تحديث Backend
gcloud run services update manus-backend \
  --region=us-central1 \
  --update-secrets=PASSWORD_SALT=password-salt:latest \
  --project=gen-lang-client-0415541083
```

### 2. ربط Frontend بـ Backend (15 دقيقة)
```bash
# SSH إلى Frontend VM
gcloud compute ssh [frontend-vm-name] --zone=us-central1-a

# تحديث environment
echo "VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app" > .env.production

# إعادة بناء
npm run build && sudo systemctl reload nginx
```

---

## 🔑 بيانات اختبار مقترحة

### بعد إعداد PASSWORD_SALT:
```
Email: test@manus.ai
Password: TestPass123!
Username: testuser
Full Name: Test User
```

---

## 📊 الحالة الحالية

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Working | < 3s startup |
| MongoDB | ✅ Connected | Via Cloud NAT |
| Redis | ⚠️ VPC Issue | Non-critical |
| Frontend | ✅ Working | Needs backend URL |
| Auth | ⚠️ Needs Salt | Registration blocked |

---

## 🎯 GCP Console

- **Backend:** https://console.cloud.google.com/run/detail/us-central1/manus-backend?project=gen-lang-client-0415541083
- **Secrets:** https://console.cloud.google.com/security/secret-manager?project=gen-lang-client-0415541083

**Project ID:** gen-lang-client-0415541083  
**Static IP:** 34.134.9.124

---

✅ **جاهز للاستخدام بعد الإعداد البسيط أعلاه!**
