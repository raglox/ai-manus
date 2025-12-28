# 🧪 Quick Test Guide - دليل الاختبار السريع

## الوصول السريع

### 🌐 Frontend (الواجهة الأمامية)
http://34.121.111.2

### 🔐 معلومات الدخول
- **Email:** demo@manus.ai
- **Password:** DemoPass123!

---

## ✅ اختبارات سريعة

### 1. اختبار Frontend

```bash
# تحقق من أن Frontend يعمل
curl -I http://34.121.111.2

# تحقق من API URL في الكود
curl -s http://34.121.111.2 | grep -o 'manus-backend[^"]*' | head -1
```

**النتيجة المتوقعة:**
- HTTP 200 OK
- API URL: `https://manus-backend-247096226016.us-central1.run.app`

---

### 2. اختبار Backend API

```bash
# Health Check
curl https://manus-backend-247096226016.us-central1.run.app/api/v1/health

# Ready Check
curl https://manus-backend-247096226016.us-central1.run.app/api/v1/ready
```

**النتيجة المتوقعة:**
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "manus-ai-backend"
}
```

---

### 3. اختبار تسجيل الدخول

```bash
curl -X POST "https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@manus.ai","password":"DemoPass123!"}'
```

**النتيجة المتوقعة:**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "user": {
      "id": "...",
      "email": "demo@manus.ai",
      "fullname": "Demo User",
      ...
    },
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

---

### 4. اختبار من المتصفح

1. **افتح:** http://34.121.111.2

2. **سجل الدخول:**
   - Email: `demo@manus.ai`
   - Password: `DemoPass123!`

3. **افتح Developer Tools (F12):**
   - اذهب إلى **Network** tab
   - سجل الدخول
   - تحقق من أن الطلبات تذهب إلى:
     `https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/login`

4. **تحقق من الـ Response:**
   - يجب أن تحصل على `access_token`
   - يجب أن يتم تحويلك إلى الصفحة الرئيسية

---

## 🐛 استكشاف الأخطاء

### المشكلة: Frontend لا يفتح

```bash
# تحقق من حالة VM
gcloud compute instances list --project=gen-lang-client-0415541083

# تحقق من logs
gcloud compute instances get-serial-port-output manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083
```

### المشكلة: API لا يستجيب

```bash
# تحقق من حالة Cloud Run
gcloud run services describe manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083

# تحقق من logs
gcloud run logs read manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083 \
  --limit=50
```

### المشكلة: تسجيل الدخول لا يعمل

1. **تحقق من Network tab في DevTools**
   - هل الطلب يذهب إلى URL الصحيح؟
   - ما هو status code؟
   - ما هو الـ response؟

2. **تحقق من Backend logs:**
```bash
gcloud run logs read manus-backend \
  --region=us-central1 \
  --project=gen-lang-client-0415541083 \
  --limit=50
```

---

## 📊 الحالة المتوقعة

✅ **Backend:**
- Status: RUNNING
- URL: https://manus-backend-247096226016.us-central1.run.app
- Health: HEALTHY
- MongoDB: CONNECTED

✅ **Frontend:**
- Status: RUNNING
- URL: http://34.121.111.2
- Nginx: ACTIVE
- API URL: Correct (points to backend)

✅ **Database:**
- MongoDB Atlas: CONNECTED
- Collections: 4 (users, agents, sessions, subscriptions)
- Users: 2 (demo, admin)

---

## 🎯 الاختبار النهائي

### خطوة بخطوة:

1. ✅ **افتح Frontend:** http://34.121.111.2
2. ✅ **صفحة Login تظهر** ← Frontend يعمل
3. ✅ **أدخل معلومات الدخول:** demo@manus.ai / DemoPass123!
4. ✅ **اضغط Login**
5. ✅ **يتم تحويلك إلى الصفحة الرئيسية** ← النظام يعمل!

---

## 🚀 النتيجة

إذا وصلت إلى هنا ونجحت جميع الاختبارات:

**🎉 تهانينا! النظام جاهز 100%!**

---

## 📚 الوثائق الكاملة

لمزيد من التفاصيل، راجع:

- **FINAL_DELIVERY.md** - التوثيق النهائي الشامل
- **PROJECT_FINAL_DELIVERY.md** - التفاصيل التقنية
- **QUICK_START.md** - دليل البدء السريع

---

**آخر تحديث:** 28 ديسمبر 2025  
**الحالة:** ✅ جاهز للاختبار
