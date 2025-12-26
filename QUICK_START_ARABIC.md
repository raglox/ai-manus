# 🚀 دليل البداية السريعة - AI Manus

## ✅ التثبيت مكتمل!

تم تثبيت وتشغيل مشروع AI Manus بنجاح على الخادم.

---

## 🌐 الوصول إلى التطبيق

### 🎨 الواجهة الأمامية
**الرابط:** http://172.245.232.188:5173

افتح هذا الرابط في المتصفح للوصول إلى واجهة المستخدم.

### 📚 توثيق API (Swagger)
**الرابط:** http://172.245.232.188:8000/docs

استكشف وجرّب APIs من خلال واجهة Swagger التفاعلية.

---

## 🔑 تسجيل الدخول

المشروع يستخدم نظام المصادقة بكلمة المرور (`AUTH_PROVIDER=password`).

لإنشاء حساب جديد:
1. افتح الواجهة الأمامية: http://172.245.232.188:5173
2. انقر على "تسجيل" أو "Sign Up"
3. أدخل بريدك الإلكتروني وكلمة المرور
4. ابدأ في استخدام AI Manus!

---

## 🛠️ أوامر إدارة المشروع

### عرض حالة الخدمات
```bash
cd /home/root/webapp
docker compose ps
```

### عرض السجلات
```bash
# جميع الخدمات
docker compose logs -f

# خدمة محددة فقط
docker compose logs -f backend
docker compose logs -f frontend
```

### إعادة تشغيل الخدمات
```bash
# إعادة تشغيل الكل
docker compose restart

# إعادة تشغيل خدمة محددة
docker compose restart backend
```

### إيقاف المشروع
```bash
docker compose down
```

### بدء المشروع مرة أخرى
```bash
docker compose up -d
```

---

## ⚙️ تعديل الإعدادات

### موقع ملف الإعدادات
```bash
/home/root/webapp/.env
```

### تعديل الإعدادات
```bash
nano /home/root/webapp/.env
```

**ملاحظة:** بعد تعديل أي إعداد، يجب إعادة تشغيل الخدمات:
```bash
cd /home/root/webapp
docker compose restart
```

### إعدادات مهمة يمكن تعديلها:

#### 1. API Key (إذا كنت تستخدم OpenAI أو Deepseek حقيقي)
```env
API_KEY=sk-your-real-api-key-here
API_BASE=https://api.openai.com/v1
```

#### 2. Model Configuration
```env
MODEL_NAME=gpt-4o  # أو deepseek-chat
TEMPERATURE=0.7
MAX_TOKENS=2000
```

#### 3. Search Provider
```env
SEARCH_PROVIDER=bing  # أو google أو baidu
```

---

## 📊 حالة الخدمات الحالية

| الخدمة | الحالة | المنفذ |
|--------|--------|--------|
| Frontend | ✅ Running | 5173 |
| Backend API | ✅ Running | 8000 |
| MongoDB | ✅ Running | 27017 |
| Redis | ✅ Running | 6379 |

---

## 🔥 الجدار الناري (Firewall)

تم إعداد القواعد التالية:
- SSH (22/tcp) ✅
- HTTP (80/tcp) ✅
- HTTPS (443/tcp) ✅
- Frontend (5173/tcp) ✅
- Backend API (8000/tcp) ✅

للتحقق من حالة الجدار الناري:
```bash
sudo ufw status verbose
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: الخدمة لا تعمل
**الحل:**
```bash
cd /home/root/webapp
docker compose ps  # تحقق من الحالة
docker compose logs backend  # فحص الأخطاء
docker compose restart  # إعادة التشغيل
```

### المشكلة: لا يمكن الوصول إلى الخدمة
**الحل:**
```bash
# تحقق من المنفذ
sudo ufw status
# إضافة المنفذ إذا لم يكن موجوداً
sudo ufw allow 5173/tcp
```

### المشكلة: استهلاك كبير للموارد
**الحل:**
```bash
# مراقبة الموارد
docker stats

# تنظيف الموارد غير المستخدمة
docker system prune -a
```

---

## 📦 النسخ الاحتياطي

### نسخ احتياطي لقاعدة البيانات
```bash
cd /home/root/webapp
docker exec webapp-mongodb-1 mongodump --out /tmp/backup
docker cp webapp-mongodb-1:/tmp/backup ./mongodb_backup_$(date +%Y%m%d)
```

### استعادة النسخة الاحتياطية
```bash
docker cp ./mongodb_backup_YYYYMMDD webapp-mongodb-1:/tmp/restore
docker exec webapp-mongodb-1 mongorestore /tmp/restore
```

---

## 📚 موارد إضافية

- **التوثيق الكامل:** `/home/root/webapp/DEPLOYMENT_SUMMARY.md`
- **README الأصلي:** `/home/root/webapp/README.md`
- **GitHub:** https://github.com/simpleyyt/ai-manus
- **الوثائق الرسمية:** https://docs.ai-manus.com

---

## 🎉 استمتع بـ AI Manus!

يمكنك الآن بدء استخدام AI Manus لتشغيل AI Agents بأدوات متنوعة في بيئة Sandbox آمنة.

**ابدأ الآن:** http://172.245.232.188:5173
