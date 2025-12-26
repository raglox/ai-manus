# 🚀 AI Manus - ملخص التثبيت والنشر

تم تثبيت ونشر مشروع AI Manus بنجاح!

## 📊 حالة الخدمات

جميع الخدمات تعمل بنجاح:

| الخدمة | الحالة | المنفذ |
|--------|--------|--------|
| Frontend | ✅ Running | 5173 |
| Backend API | ✅ Running | 8000 |
| MongoDB | ✅ Running | 27017 |
| Redis | ✅ Running | 6379 |
| Sandbox | ✅ Ready | - |

## 🌐 روابط الوصول

### 🎨 الواجهة الأمامية (Frontend)
**URL:** http://172.245.232.188:5173
- واجهة المستخدم الرئيسية لـ AI Manus
- دعم اللغة العربية والإنجليزية
- واجهة تفاعلية للتعامل مع AI Agent

### ⚙️ Backend API
**URL:** http://172.245.232.188:8000
- API الخلفي للتطبيق
- معالجة طلبات AI Agent
- إدارة Sandbox والأدوات

### 📚 API Documentation
**URL:** http://172.245.232.188:8000/docs
- توثيق تفاعلي لجميع endpoints
- واجهة Swagger UI
- إمكانية اختبار APIs مباشرة

## 🔐 الأمان

### إعدادات الأمان المطبقة:

✅ **JWT Secret Key**: تم توليد مفتاح آمن (32 حرف)
✅ **Password Salt**: تم توليد salt آمن للتشفير
✅ **Firewall Rules**: تم إعداد قواعد UFW:
  - SSH (22/tcp)
  - HTTP (80/tcp)
  - HTTPS (443/tcp)
  - Frontend (5173/tcp)
  - Backend API (8000/tcp)

### 🔥 حالة الجدار الناري:
```bash
sudo ufw status verbose
```

## 🛠️ أوامر الإدارة

### عرض حالة الخدمات:
```bash
cd /home/root/webapp
docker compose ps
```

### عرض السجلات (Logs):
```bash
# جميع الخدمات
docker compose logs -f

# خدمة محددة
docker compose logs -f backend
docker compose logs -f frontend
```

### إعادة تشغيل الخدمات:
```bash
# إعادة تشغيل خدمة واحدة
docker compose restart backend

# إعادة تشغيل جميع الخدمات
docker compose restart
```

### إيقاف المشروع:
```bash
docker compose down
```

### إيقاف وحذف البيانات:
```bash
docker compose down -v
```

### بدء المشروع مجدداً:
```bash
docker compose up -d
```

### تحديث الصور (Images):
```bash
docker compose pull
docker compose up -d
```

## 📝 الإعدادات

### موقع ملف الإعدادات:
```bash
/home/root/webapp/.env
```

### تعديل الإعدادات:
```bash
nano /home/root/webapp/.env
```

بعد تعديل الإعدادات، أعد تشغيل الخدمات:
```bash
docker compose restart
```

## 🔧 الإعدادات الحالية

### Model Configuration:
- **API_BASE**: http://mockserver:8090/v1
- **MODEL_NAME**: deepseek-chat
- **TEMPERATURE**: 0.7
- **MAX_TOKENS**: 2000

### Authentication:
- **AUTH_PROVIDER**: password
- **JWT_SECRET_KEY**: ✅ تم التكوين بشكل آمن
- **PASSWORD_SALT**: ✅ تم التكوين بشكل آمن

### Sandbox Configuration:
- **SANDBOX_IMAGE**: simpleyyt/manus-sandbox
- **SANDBOX_TTL_MINUTES**: 30
- **SANDBOX_NETWORK**: manus-network

### Search Provider:
- **SEARCH_PROVIDER**: bing

## 📊 مراقبة الموارد

### استخدام القرص:
```bash
docker system df
```

### استخدام الحاويات:
```bash
docker stats
```

## 🐛 استكشاف الأخطاء

### إذا واجهت مشاكل:

1. **تحقق من حالة الخدمات:**
```bash
docker compose ps
```

2. **فحص السجلات:**
```bash
docker compose logs backend
```

3. **إعادة بناء الحاويات:**
```bash
docker compose down
docker compose up -d --force-recreate
```

4. **تنظيف النظام:**
```bash
docker system prune -a
```

## 📦 النسخ الاحتياطي

### نسخ احتياطي لقاعدة البيانات:
```bash
docker exec webapp-mongodb-1 mongodump --out /tmp/backup
docker cp webapp-mongodb-1:/tmp/backup ./mongodb_backup
```

### استعادة النسخة الاحتياطية:
```bash
docker cp ./mongodb_backup webapp-mongodb-1:/tmp/restore
docker exec webapp-mongodb-1 mongorestore /tmp/restore
```

## 🔄 التحديثات

### تحديث المشروع:
```bash
cd /home/root/webapp
git pull origin main
docker compose pull
docker compose up -d
```

## 📞 الدعم

- **GitHub Repository**: https://github.com/simpleyyt/ai-manus
- **Documentation**: https://docs.ai-manus.com
- **QQ Group**: 1005477581

## ✅ قائمة التحقق من النشر

- [x] تثبيت Docker و Docker Compose
- [x] نسخ ملف الإعدادات (.env)
- [x] توليد مفاتيح الأمان (JWT + Password Salt)
- [x] سحب صور Docker
- [x] تشغيل جميع الخدمات
- [x] التحقق من استجابة الخدمات
- [x] إعداد قواعد الجدار الناري
- [x] الحصول على URLs العامة

## 🎉 التثبيت مكتمل!

يمكنك الآن الوصول إلى التطبيق عبر:
- **Frontend**: http://172.245.232.188:5173
- **API Docs**: http://172.245.232.188:8000/docs

استمتع باستخدام AI Manus! 🚀
