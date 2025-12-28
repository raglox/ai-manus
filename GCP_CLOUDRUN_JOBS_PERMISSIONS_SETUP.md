# GCP Cloud Run Jobs - Permissions Setup Report
# تقرير إعداد الصلاحيات لـ Cloud Run Jobs

## Executive Summary | الملخص التنفيذي

**Status**: ✅ We can create Cloud Run Jobs, but the service account needs permissions.
**الحالة**: ✅ نستطيع إنشاء Cloud Run Jobs، لكن حساب الخدمة يحتاج صلاحيات.

---

## 1. Authentication Verification | التحقق من المصادقة

✅ **Authenticated Account**: `sally.2022mm@gmail.com`
- Role: Owner (full project access)
- Can create and manage Cloud Run Jobs

---

## 2. Cloud Run Jobs API Access | الوصول لـ Cloud Run Jobs API

✅ **Successfully listed existing jobs**:
- `migrate` job - Created on 2025-12-25
- `setup` job - Created on 2025-12-25

✅ **Can describe jobs and view configuration**

---

## 3. Current Service Account | حساب الخدمة الحالي

**Service Account Used**: `automation@gen-lang-client-0415541083.iam.gserviceaccount.com`

❌ **Issue Identified**: This service account has **NO ROLES** assigned currently!

**Error Found**: When describing the migrate job:
```
Permission denied on secret: projects/247096226016/secrets/django_settings/versions/latest 
for Revision service account automation@gen-lang-client-0415541083.iam.gserviceaccount.com
```

---

## 4. Required Permissions | الصلاحيات المطلوبة

For Cloud Run Jobs sandbox implementation, the `automation` service account needs:

### Essential Roles | الصلاحيات الأساسية:

1. **Secret Manager Secret Accessor** - To access secrets
   - `roles/secretmanager.secretAccessor`

2. **Cloud Run Admin** - To manage Cloud Run Jobs
   - `roles/run.admin`

3. **Service Account User** - To act as service account
   - `roles/iam.serviceAccountUser`

4. **Artifact Registry Reader** - To pull container images
   - `roles/artifactregistry.reader`

5. **Cloud SQL Client** - For database access (if needed)
   - `roles/cloudsql.client`

6. **Logs Writer** - To write logs
   - `roles/logging.logWriter`

---

## 5. Commands to Grant Permissions | الأوامر لمنح الصلاحيات

### Option A: Run All Commands Together | تشغيل جميع الأوامر معاً

```bash
# Set project ID
PROJECT_ID="gen-lang-client-0415541083"
SERVICE_ACCOUNT="automation@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant all necessary roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter"

echo "✅ All permissions granted successfully!"
```

### Option B: Individual Commands | الأوامر الفردية

#### 1. Secret Manager Access (CRITICAL - fixes current error)
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### 2. Cloud Run Admin
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

#### 3. Service Account User
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

#### 4. Artifact Registry Reader
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.reader"
```

#### 5. Cloud SQL Client
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

#### 6. Logs Writer
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

---

## 6. Verification Command | أمر التحقق

After granting permissions, verify with:

```bash
gcloud projects get-iam-policy gen-lang-client-0415541083 \
    --flatten="bindings[].members" \
    --filter="bindings.members:automation@gen-lang-client-0415541083.iam.gserviceaccount.com" \
    --format="table(bindings.role)"
```

Expected output should show all 6 roles listed above.

---

## 7. Alternative: Create New Service Account for Sandbox

If you prefer a dedicated service account for sandbox jobs:

```bash
# Create new service account
gcloud iam service-accounts create sandbox-runner \
    --display-name="Sandbox Code Execution Service Account" \
    --project=gen-lang-client-0415541083

# Grant minimal permissions for sandbox
SERVICE_ACCOUNT="sandbox-runner@gen-lang-client-0415541083.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding gen-lang-client-0415541083 \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter"
```

---

## 8. Summary | الخلاصة

### Current Status | الوضع الحالي:
- ✅ GCP authentication working
- ✅ Cloud Run Jobs API accessible
- ✅ Can list and describe jobs
- ❌ Service account lacks necessary permissions

### Action Required | الإجراء المطلوب:
Run the commands in Section 5 to grant the required permissions.

### After Permissions | بعد منح الصلاحيات:
- ✅ Service account can access secrets
- ✅ Can create and manage Cloud Run Jobs
- ✅ Can pull container images
- ✅ Can access Cloud SQL
- ✅ Can write logs

---

## 9. Testing After Setup | الاختبار بعد الإعداد

Once permissions are granted, test by re-describing the job:

```bash
gcloud run jobs describe migrate --region=us-central1 --project=gen-lang-client-0415541083
```

The error about Secret Manager should be gone.

---

## Notes | ملاحظات

1. **User account** (`sally.2022mm@gmail.com`) has Owner role - can create/manage everything
2. **Service account** needs specific roles for automated operations
3. Existing jobs (`migrate`, `setup`) were created by compute engine service account
4. For sandbox implementation, we can use either:
   - Fix permissions for existing `automation` service account (recommended)
   - Create new dedicated `sandbox-runner` service account

---

Generated: 2025-12-28
Project: gen-lang-client-0415541083
Region: us-central1