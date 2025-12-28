# 🎯 Frontend Deployment - Manual Instructions

## 📦 الملفات جاهزة في Cloud Storage!

**موقع الملفات:**
```
gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz
```

---

## 🚀 خيارات النشر

### الخيار 1: عبر GCP Console (الأسهل)

#### الخطوة 1: افتح VM في Cloud Console
```
https://console.cloud.google.com/compute/instances
```

#### الخطوة 2: اضغط SSH على manus-frontend-vm

#### الخطوة 3: شغل هذه الأوامر في Terminal:

```bash
# Download deployment package
gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz /tmp/

# Extract
cd /tmp
tar -xzf frontend-production.tar.gz

# Backup current deployment
cp -r /usr/share/nginx/html /usr/share/nginx/html_backup

# Deploy new version
rm -rf /usr/share/nginx/html/*
cp -r /tmp/dist/* /usr/share/nginx/html/

# Set permissions
chown -R nginx:nginx /usr/share/nginx/html/ || chown -R www-data:www-data /usr/share/nginx/html/
chmod -R 755 /usr/share/nginx/html/

# Restart nginx
systemctl restart nginx

# Cleanup
rm -rf /tmp/dist /tmp/frontend-production.tar.gz

# Verify
curl -I http://localhost
```

#### الخطوة 4: اختبر
```
افتح: http://34.121.111.2
سجل دخول: demo@manus.ai / DemoPass123!
```

---

### الخيار 2: عبر Cloud Shell

```bash
# 1. Download to Cloud Shell
gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz ~/

# 2. SSH to VM and deploy
gcloud compute ssh manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083

# ثم شغل الأوامر من الخيار 1
```

---

### الخيار 3: إعادة بناء على الـ VM مباشرة

إذا كان لديك وصول SSH للـ VM:

```bash
# SSH to VM
gcloud compute ssh manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083

# On VM:
cd /root/webapp/frontend

# Create .env.production
cat > .env.production << 'EOF'
VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
EOF

# Install dependencies (if needed)
npm install

# Build
npm run build

# Deploy
rm -rf /usr/share/nginx/html/*
cp -r dist/* /usr/share/nginx/html/

# Set permissions
chown -R nginx:nginx /usr/share/nginx/html/ || chown -R www-data:www-data /usr/share/nginx/html/

# Restart nginx
systemctl restart nginx

# Verify
curl -I http://localhost
```

---

## ✅ التحقق من النشر

### 1. اختبر HTTP Response
```bash
curl -I http://34.121.111.2
# يجب أن يعطي: HTTP/1.1 200 OK
```

### 2. افتح في المتصفح
```
URL: http://34.121.111.2
```

### 3. سجل الدخول
```
Email: demo@manus.ai
Password: DemoPass123!
```

### 4. افحص Console في المتصفح (F12)
يجب أن ترى requests لـ:
```
https://manus-backend-247096226016.us-central1.run.app/api/v1/...
```

---

## 🔍 استكشاف الأخطاء

### إذا لم يعمل Frontend:

```bash
# Check nginx status
systemctl status nginx

# Check nginx error logs
tail -50 /var/log/nginx/error.log

# Check file permissions
ls -la /usr/share/nginx/html/

# Restart nginx
systemctl restart nginx
```

### إذا كان API لا يعمل:

```bash
# Test Backend directly
curl https://manus-backend-247096226016.us-central1.run.app/api/v1/health

# Check browser console for CORS errors
# Press F12 → Console tab
```

---

## 📊 الحالة الحالية

### ✅ ما يعمل:
- Backend API: https://manus-backend-247096226016.us-central1.run.app
- MongoDB: متصل
- User Auth: يعمل
- Health Checks: تعمل

### 🔧 ما يحتاج إصلاح:
- Frontend: يحتاج نشر Build الجديد (موجود في Cloud Storage)

### 📦 الملفات الجاهزة:
- Build في: `/home/root/webapp/frontend/dist/`
- Package في Cloud Storage: `gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/frontend-production.tar.gz`
- Script جاهز في Cloud Storage أيضاً

---

## 🎯 الخطوة التالية

اختر أحد الخيارات أعلاه واتبع التعليمات.  
**الخيار 1** هو الأسهل إذا كنت تستخدم GCP Console.

---

## 📞 إذا احتجت مساعدة

راجع:
- QUICK_START.md
- FINAL_DELIVERY_ARABIC.md
- DELIVERY_SUMMARY.txt

---

**🚀 بمجرد نشر Frontend، سيكون النظام 100% جاهز!**
