# 🚨 URGENT: Frontend API Fix - تحديث عاجل

## ❌ المشكلة المكتشفة:

Frontend يحاول الاتصال بـ:
```
http://34.121.111.2/api/v1/...  ❌ خطأ
```

بدلاً من:
```
https://manus-backend-247096226016.us-central1.run.app/api/v1/...  ✅ صحيح
```

---

## ✅ الحل (3 خطوات بسيطة):

### الخطوة 1: افتح GCP Console
```
https://console.cloud.google.com/compute/instances
```

### الخطوة 2: اضغط "SSH" على manus-frontend-vm

### الخطوة 3: انسخ والصق هذه الأوامر:

```bash
# تنزيل وتشغيل script الإصلاح
gsutil cp gs://gen-lang-client-0415541083_cloudbuild/frontend-deployment/fix-frontend.sh /tmp/
chmod +x /tmp/fix-frontend.sh
sudo /tmp/fix-frontend.sh
```

**هذا كل شيء!** ⚡

---

## 🧪 الاختبار بعد التحديث:

1. **افتح المتصفح**: http://34.121.111.2
2. **سجل الدخول**:
   - Email: `demo@manus.ai`
   - Password: `DemoPass123!`
3. **افحص Network في F12**:
   - يجب أن ترى requests لـ: `https://manus-backend-247096226016.us-central1.run.app`

---

## 📋 ماذا يفعل Script الإصلاح؟

1. ينزّل Frontend build الجديد من Cloud Storage
2. ينشره في `/usr/share/nginx/html/`
3. يعيد تشغيل nginx
4. ينظّف الملفات المؤقتة

---

## 🔍 إذا لم يعمل:

### الخيار البديل - بناء مباشر على الـ VM:

```bash
# على الـ VM (بعد SSH)
cd /root/webapp/frontend

# إنشاء .env.production
cat > .env.production << 'EOF'
VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app
EOF

# Build
npm install
npm run build

# Deploy
rm -rf /usr/share/nginx/html/*
cp -r dist/* /usr/share/nginx/html/
chown -R nginx:nginx /usr/share/nginx/html/ || chown -R www-data:www-data /usr/share/nginx/html/
systemctl restart nginx

# Test
curl -I http://localhost
```

---

## ✅ التحقق من النجاح:

### اختبار Backend مباشرة:
```bash
curl -X POST "https://manus-backend-247096226016.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@manus.ai","password":"DemoPass123!"}'
```
يجب أن تحصل على access_token ✅

### اختبار من Frontend:
- افتح http://34.121.111.2
- سجل دخول
- افحص Network tab في DevTools (F12)
- تأكد من requests تذهب لـ `manus-backend` URL

---

## 📞 المساعدة:

إذا واجهت مشكلة:
1. تأكد من وجود صلاحيات على الـ VM
2. تأكد من عمل nginx: `systemctl status nginx`
3. راجع nginx logs: `tail /var/log/nginx/error.log`
4. اختبر Backend مباشرة عبر curl (الأمر أعلاه)

---

## 🎯 الهدف:

بعد هذا التحديث، Frontend سيتصل بـ Backend الصحيح وسيعمل Login بنجاح! 🎉

---

**⚡ ابدأ الآن! الأوامر جاهزة للنسخ واللصق! ⚡**
