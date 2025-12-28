# 🎯 الحل الصحيح - Frontend هو Docker Container!

## 📦 المشكلة المكتشفة:

Frontend يعمل كـ **Docker container** وليس files على VM عادي!

Container config الحالي:
```yaml
image: us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
env:
  - BACKEND_URL: https://manus-backend-test-247096226016.us-central1.run.app/  # ❌ خطأ - backend قديم!
```

---

## ✅ الحل: تحديث Container Image

نحتاج:
1. بناء Frontend image جديد بـ Backend URL الصحيح
2. رفعه لـ Container Registry
3. تحديث الـ VM ليستخدم الـ image الجديد

---

## 🚀 الخطوات (على الـ Sandbox المحلي):

### الخطوة 1: بناء Docker image للـ Frontend

```bash
cd /home/root/webapp/frontend

# إنشاء Dockerfile
cat > Dockerfile << 'EOF'
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Set API URL
ENV VITE_API_URL=https://manus-backend-247096226016.us-central1.run.app

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config (if exists)
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || true

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# إنشاء nginx.conf
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass https://manus-backend-247096226016.us-central1.run.app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
```

### الخطوة 2: Build و Push الـ image

```bash
export PATH="/tmp/google-cloud-sdk/bin:$PATH"
cd /home/root/webapp/frontend

# Build
gcloud builds submit --tag us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest \
  --project=gen-lang-client-0415541083

# أو استخدم docker مباشرة
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest .
docker push us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest
```

### الخطوة 3: تحديث الـ VM

```bash
# إيقاف الـ VM
gcloud compute instances stop manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083

# تحديث container config
gcloud compute instances update-container manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083 \
  --container-image=us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest \
  --container-env=BACKEND_URL=https://manus-backend-247096226016.us-central1.run.app

# تشغيل الـ VM
gcloud compute instances start manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083
```

---

## ⚡ الحل السريع (Alternative):

إذا كان الـ frontend image موجود أصلاً، فقط حدث environment variable:

```bash
gcloud compute instances update-container manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083 \
  --container-env=BACKEND_URL=https://manus-backend-247096226016.us-central1.run.app \
  --container-restart-policy=always
```

ثم أعد تشغيل الـ VM:

```bash
gcloud compute instances reset manus-frontend-vm \
  --zone=us-central1-a \
  --project=gen-lang-client-0415541083
```

---

## 🧪 الاختبار:

بعد 1-2 دقيقة:
```bash
curl http://34.121.111.2
```

ثم افتح في المتصفح: http://34.121.111.2

---

## 📝 ملاحظات:

- Frontend يعمل كـ Docker container على Container-Optimized OS
- لا يمكن تعديل files مباشرة على الـ VM
- يجب بناء image جديد ورفعه لـ Container Registry
- ثم تحديث الـ VM ليستخدم الـ image الجديد

---

**🚀 ابدأ بالحل السريع (تحديث ENV variable) أولاً!**
