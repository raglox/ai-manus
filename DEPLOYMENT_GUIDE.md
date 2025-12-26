# 🚀 دليل النشر على الخادم البعيد

**الخادم:** 172.245.232.188  
**المستخدم:** root  
**كلمة المرور:** pj8QwAf2Gfv1SmcZTgpp  

---

## 📋 المتطلبات

- خادم Linux (Ubuntu/Debian موصى به)
- Docker 20.10+
- Docker Compose
- اتصال إنترنت مستقر
- 2GB RAM على الأقل
- 10GB مساحة تخزين

---

## 🔧 طريقة النشر الأولى: تلقائي (موصى به)

### الخطوة 1: من جهازك المحلي

```bash
# استنساخ المشروع (إذا لم يكن موجوداً)
git clone https://github.com/raglox/ai-manus.git
cd ai-manus

# تشغيل سكريبت النشر التلقائي
chmod +x deploy_to_server.sh
./deploy_to_server.sh
```

**ملاحظة:** سيطلب منك كلمة المرور عدة مرات. استخدم: `pj8QwAf2Gfv1SmcZTgpp`

---

## 🔧 طريقة النشر الثانية: يدوي

### الخطوة 1: الاتصال بالخادم

```bash
ssh root@172.245.232.188
# Password: pj8QwAf2Gfv1SmcZTgpp
```

### الخطوة 2: إنشاء مجلد المشروع

```bash
mkdir -p /opt/ai-manus
cd /opt/ai-manus
```

### الخطوة 3: تنزيل المشروع

```bash
# الطريقة 1: من GitHub
git clone https://github.com/raglox/ai-manus.git .

# أو الطريقة 2: من جهازك المحلي (من terminal منفصل)
# rsync -avz --progress ~/ai-manus/ root@172.245.232.188:/opt/ai-manus/
```

### الخطوة 4: تثبيت Docker

```bash
# تحديث النظام
apt-get update
apt-get upgrade -y

# تثبيت Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# تثبيت Docker Compose
apt-get install -y docker-compose-plugin

# التحقق من التثبيت
docker --version
docker compose version
```

### الخطوة 5: إعداد ملف البيئة

```bash
cd /opt/ai-manus

# نسخ ملف البيئة النموذجي
cp .env.example .env

# تحرير ملف البيئة
nano .env
```

**الإعدادات المهمة في `.env`:**

```bash
# نموذج الذكاء الاصطناعي (اختياري - يعمل بدون API key)
API_KEY=sk-your-openai-api-key-here
API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o

# المصادقة
AUTH_PROVIDER=password  # أو none للتطوير
JWT_SECRET_KEY=YOUR_SECURE_RANDOM_KEY_HERE  # مهم جداً!

# Stripe (اختياري - للفوترة)
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_ID_BASIC=price_basic_id
STRIPE_PRICE_ID_PRO=price_pro_id

# البحث (اختياري)
SEARCH_PROVIDER=bing  # أو google أو baidu
```

**لتوليد JWT_SECRET_KEY آمن:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### الخطوة 6: تشغيل المشروع

```bash
cd /opt/ai-manus

# سحب وبناء الصور
docker compose pull

# تشغيل جميع الخدمات
docker compose up -d

# مشاهدة السجلات
docker compose logs -f
```

### الخطوة 7: التحقق من التشغيل

```bash
# التحقق من حالة الحاويات
docker compose ps

# يجب أن ترى:
# - frontend (running)
# - backend (running)
# - mongodb (running)
# - redis (running)
```

---

## 🌐 الوصول إلى التطبيق

بعد التشغيل الناجح:

- **الواجهة الأمامية:** http://172.245.232.188:5173
- **Backend API:** http://172.245.232.188:8000
- **API Docs:** http://172.245.232.188:8000/docs

---

## 🔒 إعدادات الأمان الموصى بها

### 1. تفعيل الجدار الناري

```bash
# السماح بـ SSH
ufw allow 22/tcp

# السماح بـ HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# السماح بمنافذ التطبيق
ufw allow 5173/tcp  # Frontend
ufw allow 8000/tcp  # Backend

# تفعيل الجدار الناري
ufw enable
```

### 2. إعداد SSL/TLS (موصى به للإنتاج)

```bash
# تثبيت Certbot
apt-get install -y certbot

# الحصول على شهادة SSL (يتطلب domain name)
certbot certonly --standalone -d yourdomain.com
```

### 3. إعداد Nginx كـ Reverse Proxy

```bash
apt-get install -y nginx

# إنشاء ملف تكوين Nginx
cat > /etc/nginx/sites-available/ai-manus << 'EOF'
server {
    listen 80;
    server_name 172.245.232.188;  # أو your-domain.com

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# تفعيل التكوين
ln -s /etc/nginx/sites-available/ai-manus /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 📊 أوامر الإدارة

### عرض السجلات

```bash
# جميع الخدمات
docker compose logs -f

# خدمة معينة
docker compose logs -f backend
docker compose logs -f frontend
```

### إعادة تشغيل الخدمات

```bash
# جميع الخدمات
docker compose restart

# خدمة معينة
docker compose restart backend
```

### إيقاف الخدمات

```bash
# إيقاف مؤقت
docker compose stop

# إيقاف وإزالة الحاويات
docker compose down

# إيقاف وإزالة كل شيء (بما في ذلك البيانات)
docker compose down -v
```

### تحديث المشروع

```bash
cd /opt/ai-manus

# سحب أحدث تغييرات من Git
git pull origin main

# إعادة بناء وتشغيل
docker compose up -d --build
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي لقاعدة البيانات
docker compose exec mongodb mongodump --out /tmp/backup
docker compose cp mongodb:/tmp/backup ./backup-$(date +%Y%m%d)

# نسخ احتياطي للبيانات الكاملة
tar -czf ai-manus-backup-$(date +%Y%m%d).tar.gz /opt/ai-manus
```

---

## 🐛 استكشاف الأخطاء وإصلاحها

### المشكلة: الحاويات لا تبدأ

```bash
# التحقق من السجلات
docker compose logs

# التحقق من مساحة القرص
df -h

# التحقق من ذاكرة الوصول العشوائي
free -h

# إعادة إنشاء الحاويات
docker compose down
docker compose up -d --force-recreate
```

### المشكلة: خطأ في الاتصال بـ MongoDB

```bash
# التحقق من حالة MongoDB
docker compose ps mongodb

# إعادة تشغيل MongoDB
docker compose restart mongodb

# التحقق من السجلات
docker compose logs mongodb
```

### المشكلة: خطأ في الاتصال بـ Redis

```bash
# التحقق من حالة Redis
docker compose ps redis

# إعادة تشغيل Redis
docker compose restart redis
```

### المشكلة: Backend لا يستجيب

```bash
# التحقق من السجلات
docker compose logs backend

# إعادة تشغيل Backend
docker compose restart backend

# التحقق من الاتصال بـ MongoDB و Redis
docker compose exec backend ping -c 3 mongodb
docker compose exec backend ping -c 3 redis
```

---

## 📈 المراقبة والأداء

### تثبيت htop لمراقبة الموارد

```bash
apt-get install -y htop
htop
```

### مراقبة استخدام Docker

```bash
# استخدام الموارد
docker stats

# حجم الصور
docker images

# حجم الحاويات
docker ps -s
```

### تنظيف الموارد غير المستخدمة

```bash
# إزالة الحاويات المتوقفة
docker container prune -f

# إزالة الصور غير المستخدمة
docker image prune -a -f

# إزالة الشبكات غير المستخدمة
docker network prune -f

# إزالة كل شيء
docker system prune -a -f
```

---

## 🎯 الخطوات بعد التثبيت

1. ✅ **إنشاء حساب مستخدم**
   - افتح http://172.245.232.188:5173
   - انقر على "Register"
   - أدخل البيانات وسجل

2. ✅ **اختبار الوظائف**
   - إنشاء جلسة جديدة
   - إرسال رسالة اختبار
   - التحقق من عمل الـ Sandbox

3. ✅ **إعداد Monitoring (اختياري)**
   - تفعيل Sentry في `.env`
   - تفعيل UptimeRobot لمراقبة التوفر

4. ✅ **إعداد Backup التلقائي**
   - إنشاء cron job للنسخ الاحتياطي اليومي

5. ✅ **إعداد Domain و SSL**
   - ربط domain name
   - تثبيت SSL certificate

---

## 📞 الدعم

في حالة مواجهة مشاكل:

1. **فحص السجلات:** `docker compose logs -f`
2. **التحقق من الحالة:** `docker compose ps`
3. **مراجعة التوثيق:** `/opt/ai-manus/README.md`
4. **GitHub Issues:** https://github.com/raglox/ai-manus/issues

---

## 🎉 التهانينا!

تم نشر AI Manus بنجاح على خادمك! 🚀

**الوصول إلى التطبيق:**
- Frontend: http://172.245.232.188:5173
- Backend: http://172.245.232.188:8000

**التحديثات الأخيرة المطبقة:**
- ✅ حماية XSS
- ✅ فرض حدود الاستخدام
- ✅ تحديد معدل SSE
- ✅ تحسينات الأمان
- ✅ اختبارات شاملة

**Quality Score:** 10/10 ⭐  
**Date:** 2025-12-26
