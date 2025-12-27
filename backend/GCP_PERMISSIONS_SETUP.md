# 🔐 إعداد صلاحيات Google Cloud للنشر

## 📋 معلومات المشروع
- **Project ID**: `gen-lang-client-0415541083`
- **Service Account**: `vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com`

---

## ⚡ نسخ ولصق - جاهز للتنفيذ

### الخطوة 1: تفعيل APIs المطلوبة

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=gen-lang-client-0415541083
```

---

### الخطوة 2: إعطاء صلاحيات الـ Service Account

انسخ الأوامر التالية وقم بتنفيذها **مرة واحدة** من Google Cloud Shell أو من terminal حسابك:

```bash
# 1. Cloud Run Admin - لإدارة خدمات Cloud Run
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# 2. Artifact Registry Admin - لرفع وإدارة Docker images
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

# 3. Cloud Build Editor - لبناء Docker images
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# 4. Secret Manager Admin - لإدارة المفاتيح السرية
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

# 5. Service Account User - لاستخدام Service Accounts
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 6. Storage Admin - لإدارة التخزين والـ artifacts
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 7. Service Usage Admin - لتفعيل الـ APIs
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageAdmin"

# 8. Compute Admin - للوصول إلى موارد الحوسبة
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="roles/compute.admin"
```

---

## 🎯 أوامر واحدة - نسخ ولصق

إذا أردت تنفيذ كل شيء دفعة واحدة:

```bash
# تعيين متغيرات
PROJECT_ID="gen-lang-client-0415541083"
SERVICE_ACCOUNT="vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com"

# تفعيل APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=$PROJECT_ID

echo "✅ APIs enabled"

# إعطاء جميع الصلاحيات
for ROLE in \
  "roles/run.admin" \
  "roles/artifactregistry.admin" \
  "roles/cloudbuild.builds.editor" \
  "roles/secretmanager.admin" \
  "roles/iam.serviceAccountUser" \
  "roles/storage.admin" \
  "roles/serviceusage.serviceUsageAdmin" \
  "roles/compute.admin"
do
  echo "Adding role: $ROLE"
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="$ROLE" \
    --quiet
done

echo "✅ All permissions granted"
```

---

## 📊 قائمة الصلاحيات المطلوبة

| الصلاحية (Role) | السبب | مطلوبة؟ |
|-----------------|--------|---------|
| `roles/run.admin` | إنشاء وإدارة Cloud Run services | ✅ إلزامي |
| `roles/artifactregistry.admin` | رفع Docker images | ✅ إلزامي |
| `roles/cloudbuild.builds.editor` | بناء Docker images | ✅ إلزامي |
| `roles/secretmanager.admin` | إدارة المفاتيح السرية | ✅ إلزامي |
| `roles/iam.serviceAccountUser` | استخدام Service Accounts | ✅ إلزامي |
| `roles/storage.admin` | إدارة التخزين | ✅ إلزامي |
| `roles/serviceusage.serviceUsageAdmin` | تفعيل APIs | ✅ إلزامي |
| `roles/compute.admin` | موارد الحوسبة | ⚠️ موصى به |

---

## 🔍 التحقق من الصلاحيات

بعد تنفيذ الأوامر، تحقق من الصلاحيات:

```bash
gcloud projects get-iam-policy gen-lang-client-0415541083 \
  --flatten="bindings[].members" \
  --filter="bindings.members:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

يجب أن ترى:
```
ROLE
roles/artifactregistry.admin
roles/cloudbuild.builds.editor
roles/compute.admin
roles/iam.serviceAccountUser
roles/run.admin
roles/secretmanager.admin
roles/serviceusage.serviceUsageAdmin
roles/storage.admin
```

---

## 🚀 طرق التنفيذ

### الطريقة 1: Google Cloud Console (الأسهل)

1. اذهب إلى: https://console.cloud.google.com/iam-admin/iam?project=gen-lang-client-0415541083
2. ابحث عن `vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com`
3. اضغط "Edit" (قلم رصاص)
4. اضغط "+ ADD ANOTHER ROLE"
5. أضف الصلاحيات التالية واحدة تلو الأخرى:
   - Cloud Run Admin
   - Artifact Registry Administrator
   - Cloud Build Editor
   - Secret Manager Admin
   - Service Account User
   - Storage Admin
   - Service Usage Admin
   - Compute Admin
6. اضغط "Save"

---

### الطريقة 2: Google Cloud Shell

1. اذهب إلى: https://console.cloud.google.com/?cloudshell=true
2. انقر على أيقونة Cloud Shell (في الأعلى)
3. انسخ والصق الأوامر من القسم "أوامر واحدة" أعلاه
4. اضغط Enter

---

### الطريقة 3: Local Terminal (من حاسوبك)

إذا كان لديك gcloud مثبت على حاسوبك:

```bash
# 1. تسجيل الدخول
gcloud auth login

# 2. تعيين المشروع
gcloud config set project gen-lang-client-0415541083

# 3. نسخ ولصق الأوامر من أعلاه
```

---

## ⏱️ كم يستغرق؟

- **تفعيل APIs**: 2-3 دقائق
- **إعطاء الصلاحيات**: 1-2 دقائق
- **التحقق**: 30 ثانية
- **الإجمالي**: ~5 دقائق

---

## ❓ أسئلة شائعة

### س: هل هذه الصلاحيات آمنة؟
**ج**: نعم، هذه صلاحيات قياسية للنشر. Service Account محدود بمشروعك فقط.

### س: هل يمكنني إعطاء صلاحيات أقل؟
**ج**: نعم، لكن قد تواجه أخطاء أثناء النشر. يمكنك البدء بالصلاحيات الأساسية:
- `roles/run.admin`
- `roles/artifactregistry.admin`
- `roles/secretmanager.admin`

### س: كيف أزيل الصلاحيات لاحقاً؟
**ج**: استخدم:
```bash
gcloud projects remove-iam-policy-binding gen-lang-client-0415541083 \
  --member="serviceAccount:vertex-express@gen-lang-client-0415541083.iam.gserviceaccount.com" \
  --role="ROLE_NAME"
```

### س: هل أحتاج Billing account؟
**ج**: نعم، تحتاج Billing account مفعّل للمشروع. Free tier يكفي للبدء.

---

## 🎬 بعد الانتهاء

عند اكتمال جميع الصلاحيات، أخبرني وسأكمل النشر تلقائياً! 🚀

---

## 📞 إذا واجهت مشاكل

### خطأ: "Permission denied"
- تأكد أنك مسجل دخول بحساب Owner/Editor للمشروع
- تحقق من Billing account مفعّل

### خطأ: "API not enabled"
- قم بتفعيل الـ API يدوياً من Console:
  https://console.cloud.google.com/apis/library?project=gen-lang-client-0415541083

### خطأ: "Quota exceeded"
- تحقق من Quotas:
  https://console.cloud.google.com/iam-admin/quotas?project=gen-lang-client-0415541083

---

**✅ جاهز؟ بعد تنفيذ هذه الأوامر، أخبرني وسأكمل النشر!**
