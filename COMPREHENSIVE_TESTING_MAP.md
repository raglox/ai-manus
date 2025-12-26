# 🗺️ خريطة اختبارات AI Manus الشاملة
## مبنية على جميع التعديلات والإصلاحات المنفذة

**التاريخ**: 26 ديسمبر 2025  
**الحالة**: 📋 خريطة شاملة للمشروع الكامل  
**النطاق**: Backend + Frontend + Infrastructure + Integration

---

## 📊 ملخص تنفيذي

### نظرة عامة على المشروع

| المكون | التقنية | الحالة | خطوط الكود | التغطية الحالية |
|--------|---------|--------|------------|-----------------|
| **Backend** | Python 3.12 + FastAPI | ✅ عامل | ~4,000 | 20.93% |
| **Frontend** | Vue 3 + TypeScript | ✅ عامل | ~8,000 | 0% |
| **Infrastructure** | Docker + Nginx + Redis | ✅ عامل | ~500 | 0% |
| **Database** | MongoDB 7.0 | ✅ عامل | - | N/A |
| **Sandbox** | Ubuntu + Playwright | ✅ عامل | - | N/A |

### الإصلاحات الرئيسية المنفذة

1. ✅ **Rate Limiting Decorator Error** - إزالة decorators متعارضة
2. ✅ **XSS Protection** - إضافة مكتبة Bleach
3. ✅ **Unterminated String** - إصلاح docstring
4. ✅ **Port Conflict** - تغيير Backend إلى 8002
5. ✅ **Nginx Proxy** - إصلاح تمرير Authorization header
6. ✅ **BillingMiddleware** - تعطيل مؤقت حتى الإصلاح الكامل

---

## 🏗️ بنية الاختبارات المقترحة

```
tests/
├── backend/                        # 🐍 اختبارات Backend
│   ├── unit/                       # اختبارات الوحدة
│   │   ├── services/               # الخدمات
│   │   ├── models/                 # النماذج
│   │   ├── middleware/             # Middleware
│   │   ├── repositories/           # المستودعات
│   │   └── utils/                  # الأدوات المساعدة
│   ├── integration/                # اختبارات التكامل
│   │   ├── api/                    # API endpoints
│   │   ├── database/               # MongoDB operations
│   │   ├── cache/                  # Redis operations
│   │   └── external/               # External services
│   └── e2e/                        # اختبارات End-to-End
│       ├── auth_flow/              # سيناريوهات المصادقة
│       ├── agent_workflow/         # سيناريوهات الـ AI Agent
│       └── session_management/     # إدارة الجلسات
│
├── frontend/                       # 🎨 اختبارات Frontend
│   ├── unit/                       # اختبارات الوحدة
│   │   ├── components/             # مكونات Vue
│   │   ├── composables/            # Composables
│   │   ├── utils/                  # الأدوات المساعدة
│   │   └── api/                    # API clients
│   ├── integration/                # اختبارات التكامل
│   │   ├── views/                  # الصفحات الكاملة
│   │   ├── routing/                # Vue Router
│   │   └── store/                  # State management
│   └── e2e/                        # اختبارات End-to-End
│       ├── cypress/                # Cypress tests
│       └── playwright/             # Playwright tests
│
├── infrastructure/                 # 🔧 اختبارات البنية التحتية
│   ├── docker/                     # Docker configuration tests
│   ├── nginx/                      # Nginx configuration tests
│   ├── mongodb/                    # Database tests
│   └── redis/                      # Cache tests
│
└── integration_full/               # 🔗 اختبارات التكامل الكامل
    ├── user_journeys/              # رحلات المستخدم الكاملة
    ├── performance/                # اختبارات الأداء
    ├── security/                   # اختبارات الأمان
    └── load/                       # اختبارات الحمل
```

---

## 🐍 Backend Testing Map (تفصيلي)

### 1. Application Layer (Services)

#### 1.1 Authentication Service ✅ (تم إنشاء الاختبارات)
**الملف**: `app/application/services/auth_service.py` (184 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_register_success` - تسجيل مستخدم جديد
- ✅ `test_register_duplicate_email` - رفض بريد مكرر
- ✅ `test_register_weak_password` - رفض كلمة مرور ضعيفة
- ✅ `test_login_success` - تسجيل دخول ناجح
- ✅ `test_login_wrong_password` - رفض كلمة مرور خاطئة
- ✅ `test_login_inactive_user` - رفض مستخدم غير نشط
- ✅ `test_change_password` - تغيير كلمة المرور
- ✅ `test_verify_token` - التحقق من التوكن
- ✅ `test_refresh_token` - تجديد التوكن
- ✅ `test_logout` - تسجيل الخروج

**التعديلات المرتبطة**:
- إزالة `@limiter.limit` decorators من auth_routes.py
- إصلاح unterminated string في docstring

#### 1.2 Token Service ✅ (تم إنشاء الاختبارات)
**الملف**: `app/application/services/token_service.py` (124 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_generate_access_token` - توليد access token
- ✅ `test_generate_refresh_token` - توليد refresh token
- ✅ `test_verify_valid_token` - تحقق من توكن صحيح
- ✅ `test_verify_expired_token` - رفض توكن منتهي
- ✅ `test_verify_invalid_token` - رفض توكن غير صحيح
- ✅ `test_get_user_from_token` - استخراج بيانات المستخدم
- ✅ `test_blacklist_token` - إضافة إلى القائمة السوداء

**التكامل مع**:
- JWT_SECRET_KEY (32 حرف آمن)
- Redis للـ blacklist

#### 1.3 Session Service (جديد - يحتاج إنشاء)
**الملف**: `app/application/services/session_service.py`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_create_session` - إنشاء جلسة جديدة
- ⏳ `test_list_user_sessions` - عرض جلسات المستخدم
- ⏳ `test_get_session_by_id` - جلب جلسة محددة
- ⏳ `test_delete_session` - حذف جلسة
- ⏳ `test_stop_session` - إيقاف جلسة
- ⏳ `test_session_status_transitions` - انتقالات الحالات
- ⏳ `test_session_events` - إدارة أحداث الجلسة
- ⏳ `test_session_sharing` - مشاركة الجلسات

**التعديلات المرتبطة**:
- إزالة `@limiter.limit` من session_routes.py
- إصلاح 401 Unauthorized مع BillingMiddleware

#### 1.4 File Service
**الملف**: `app/application/services/file_service.py` (86 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🟡 عالية

**الاختبارات المطلوبة**:
- ⏳ `test_upload_file` - رفع ملف
- ⏳ `test_download_file` - تحميل ملف
- ⏳ `test_delete_file` - حذف ملف
- ⏳ `test_list_user_files` - عرض ملفات المستخدم
- ⏳ `test_file_validation` - التحقق من الملفات
- ⏳ `test_file_size_limits` - حدود الحجم
- ⏳ `test_supported_file_types` - أنواع الملفات المدعومة

### 2. Domain Layer (Models & Repositories)

#### 2.1 User Model ✅ (تم إنشاء الاختبارات)
**الملف**: `app/domain/models/user.py` (38 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_user_creation` - إنشاء نموذج مستخدم
- ✅ `test_user_validation` - التحقق من البيانات
- ✅ `test_user_defaults` - القيم الافتراضية
- ✅ `test_user_equality` - مقارنة المستخدمين

#### 2.2 Subscription Model ✅ (تم إنشاء الاختبارات)
**الملف**: `app/domain/models/subscription.py` (89 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_subscription_creation` - إنشاء اشتراك
- ✅ `test_can_use_agent` - التحقق من الحدود
- ✅ `test_increment_usage` - زيادة الاستخدام
- ✅ `test_reset_monthly_usage` - إعادة تعيين شهري
- ✅ `test_subscription_plans` - خطط الاشتراك
- ✅ `test_subscription_statuses` - حالات الاشتراك

**التعديلات المرتبطة**:
- تعطيل BillingMiddleware مؤقتاً

#### 2.3 Session Model ✅ (تم إنشاء الاختبارات)
**الملف**: `app/domain/models/session.py` (34 سطر)  
**التغطية الحالية**: 88.24%  
**الأولوية**: 🟢 جيدة (تحسين)

**الاختبارات الإضافية**:
- ✅ `test_session_with_events` - جلسة مع أحداث
- ✅ `test_session_status_enum` - تعدادات الحالات

### 3. Infrastructure Layer (Middleware)

#### 3.1 Billing Middleware ⚠️ (معطل حالياً)
**الملف**: `app/infrastructure/middleware/billing_middleware.py` (57 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة (بحاجة إصلاح أولاً)

**الاختبارات المطلوبة**:
- ⏳ `test_allows_health_endpoints` - السماح بـ health
- ⏳ `test_allows_auth_endpoints` - السماح بـ auth
- ⏳ `test_blocks_without_user_id` - رفض بدون user_id
- ⏳ `test_allows_with_valid_subscription` - السماح مع اشتراك صحيح
- ⏳ `test_blocks_without_subscription` - رفض بدون اشتراك
- ⏳ `test_blocks_exceeded_limit` - رفض تجاوز الحد
- ⏳ `test_increments_usage` - زيادة عداد الاستخدام

**التعديلات المرتبطة**:
- تعطيل في main.py (السطر 103-107)
- TODO: إنشاء AuthenticationMiddleware قبله

#### 3.2 Rate Limiting Middleware
**الملف**: `app/infrastructure/middleware/rate_limit.py` (23 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🟡 عالية

**الاختبارات المطلوبة**:
- ⏳ `test_allows_within_limit` - السماح ضمن الحد
- ⏳ `test_blocks_exceeded_limit` - رفض تجاوز الحد
- ⏳ `test_rate_limit_per_ip` - حد لكل IP
- ⏳ `test_rate_limit_per_user` - حد لكل مستخدم
- ⏳ `test_redis_backend` - تكامل مع Redis

**التكامل مع**:
- Redis على المنفذ 6379
- SimpleRateLimiter في main.py

### 4. Interface Layer (API Routes)

#### 4.1 Auth Routes ✅ (اختبارات تكامل منشأة)
**الملف**: `app/interfaces/api/auth_routes.py`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_register_endpoint` - POST /auth/register
- ✅ `test_login_endpoint` - POST /auth/login
- ✅ `test_logout_endpoint` - POST /auth/logout
- ✅ `test_refresh_endpoint` - POST /auth/refresh
- ✅ `test_get_current_user` - GET /auth/me
- ✅ `test_change_password` - POST /auth/change-password

**التعديلات المرتبطة**:
- إزالة `@limiter.limit` decorators
- إصلاح unterminated string في docstring

#### 4.2 Session Routes ✅ (اختبارات تكامل منشأة)
**الملف**: `app/interfaces/api/session_routes.py`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ✅ `test_create_session` - PUT /sessions
- ✅ `test_list_sessions` - GET /sessions
- ✅ `test_get_session` - GET /sessions/{id}
- ✅ `test_delete_session` - DELETE /sessions/{id}
- ✅ `test_stop_session` - POST /sessions/{id}/stop
- ✅ `test_chat_endpoint` - POST /sessions/{id}/chat
- ✅ `test_stream_sessions` - POST /sessions (SSE)

**التعديلات المرتبطة**:
- إزالة `@limiter.limit` من stream_sessions و chat
- إصلاح 401 مع BillingMiddleware

### 5. Utils & Security

#### 5.1 Sanitizer (XSS Protection)
**الملف**: `app/application/utils/sanitizer.py` (57 سطر)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة (أمان)

**الاختبارات المطلوبة**:
- ⏳ `test_sanitize_html` - تنظيف HTML
- ⏳ `test_prevent_xss_script` - منع script tags
- ⏳ `test_prevent_xss_event_handlers` - منع event handlers
- ⏳ `test_allow_safe_tags` - السماح بـ tags آمنة
- ⏳ `test_bleach_integration` - تكامل مع Bleach

**التعديلات المرتبطة**:
- إضافة `bleach>=6.0.0` إلى requirements.txt

---

## 🎨 Frontend Testing Map (تفصيلي)

### 1. Components (مكونات Vue)

#### 1.1 Authentication Components
**الملفات**: `src/components/login/*`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_login_form_rendering` - عرض نموذج الدخول
- ⏳ `test_login_form_validation` - التحقق من المدخلات
- ⏳ `test_login_success` - دخول ناجح
- ⏳ `test_login_failure` - فشل الدخول
- ⏳ `test_register_form` - نموذج التسجيل
- ⏳ `test_password_visibility_toggle` - إظهار/إخفاء كلمة المرور

#### 1.2 Chat Components
**الملفات**:
- `src/components/ChatBox.vue`
- `src/components/ChatMessage.vue`
- `src/components/ChatBoxFiles.vue`

**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_chat_box_rendering` - عرض صندوق الدردشة
- ⏳ `test_send_message` - إرسال رسالة
- ⏳ `test_receive_message` - استقبال رسالة
- ⏳ `test_message_formatting` - تنسيق الرسائل
- ⏳ `test_file_attachments` - المرفقات
- ⏳ `test_sse_connection` - اتصال SSE
- ⏳ `test_typing_indicator` - مؤشر الكتابة

#### 1.3 Session Components
**الملفات**:
- `src/components/SessionItem.vue`
- `src/components/SessionFileList.vue`
- `src/components/LeftPanel.vue`

**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_session_list_rendering` - عرض قائمة الجلسات
- ⏳ `test_create_new_session` - إنشاء جلسة جديدة
- ⏳ `test_select_session` - اختيار جلسة
- ⏳ `test_delete_session` - حذف جلسة
- ⏳ `test_session_status_display` - عرض حالة الجلسة
- ⏳ `test_unread_message_count` - عداد الرسائل غير المقروءة

#### 1.4 File Components
**الملفات**:
- `src/components/FilePanel.vue`
- `src/components/FilePanelContent.vue`
- `src/components/filePreview/*`

**التغطية الحالية**: 0%  
**الأولوية**: 🟡 عالية

**الاختبارات المطلوبة**:
- ⏳ `test_file_upload` - رفع ملف
- ⏳ `test_file_preview` - معاينة ملف
- ⏳ `test_file_download` - تحميل ملف
- ⏳ `test_file_delete` - حذف ملف
- ⏳ `test_file_type_icons` - أيقونات أنواع الملفات
- ⏳ `test_file_size_validation` - التحقق من حجم الملف

### 2. Composables (منطق قابل لإعادة الاستخدام)

#### 2.1 Authentication Composable
**الملف**: `src/composables/useAuth.ts`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_login_composable` - وظيفة الدخول
- ⏳ `test_logout_composable` - وظيفة الخروج
- ⏳ `test_token_storage` - تخزين التوكن
- ⏳ `test_token_refresh` - تجديد التوكن
- ⏳ `test_auth_state_management` - إدارة حالة المصادقة

#### 2.2 Agent Stream Composable
**الملف**: `src/composables/useAgentStream.ts`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_sse_connection` - اتصال SSE
- ⏳ `test_event_parsing` - تحليل الأحداث
- ⏳ `test_connection_error_handling` - معالجة أخطاء الاتصال
- ⏳ `test_reconnection_logic` - منطق إعادة الاتصال

#### 2.3 File Panel Composable
**الملف**: `src/composables/useFilePanel.ts`  
**التغطية الحالية**: 0%  
**الأولوية**: 🟡 عالية

**الاختبارات المطلوبة**:
- ⏳ `test_file_list_management` - إدارة قائمة الملفات
- ⏳ `test_file_selection` - اختيار الملفات
- ⏳ `test_panel_visibility_toggle` - إظهار/إخفاء اللوحة

### 3. API Clients

#### 3.1 Authentication API Client
**الملف**: `src/api/auth.ts` (مفترض)  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_login_api_call` - استدعاء API للدخول
- ⏳ `test_register_api_call` - استدعاء API للتسجيل
- ⏳ `test_refresh_token_api_call` - استدعاء API لتجديد التوكن
- ⏳ `test_error_handling` - معالجة الأخطاء
- ⏳ `test_interceptors` - مقاطعات HTTP

### 4. Utils

#### 4.1 Authentication Utils
**الملف**: `src/utils/auth.ts`  
**التغطية الحالية**: 0%  
**الأولوية**: 🔴 حرجة

**الاختبارات المطلوبة**:
- ⏳ `test_token_validation` - التحقق من التوكن
- ⏳ `test_token_expiry_check` - فحص انتهاء التوكن
- ⏳ `test_token_decode` - فك تشفير التوكن

#### 4.2 Time Utils
**الملف**: `src/utils/time.ts`  
**التغطية الحالية**: 0%  
**الأولوية**: 🟢 منخفضة

**الاختبارات المطلوبة**:
- ⏳ `test_format_time` - تنسيق الوقت
- ⏳ `test_relative_time` - الوقت النسبي
- ⏳ `test_timezone_handling` - معالجة المناطق الزمنية

---

## 🔧 Infrastructure Testing Map

### 1. Docker Configuration Tests

#### 1.1 Docker Compose Configuration
**الملفات**:
- `docker-compose.production.yml`
- `docker-compose.yml`

**الاختبارات المطلوبة**:
- ⏳ `test_all_services_defined` - جميع الخدمات معرفة
- ⏳ `test_network_configuration` - تكوين الشبكة
- ⏳ `test_volume_mounts` - تثبيت المجلدات
- ⏳ `test_environment_variables` - متغيرات البيئة
- ⏳ `test_port_mappings` - تعيين المنافذ
- ⏳ `test_service_dependencies` - تبعيات الخدمات

#### 1.2 Backend Dockerfile
**الملف**: `backend/Dockerfile`

**الاختبارات المطلوبة**:
- ⏳ `test_base_image` - صورة الأساس
- ⏳ `test_dependencies_installation` - تثبيت التبعيات
- ⏳ `test_bleach_package_present` - وجود مكتبة Bleach
- ⏳ `test_working_directory` - مجلد العمل
- ⏳ `test_exposed_ports` - المنافذ المكشوفة

#### 1.3 Frontend Dockerfile
**الملف**: `frontend/Dockerfile`

**الاختبارات المطلوبة**:
- ⏳ `test_multi_stage_build` - بناء متعدد المراحل
- ⏳ `test_node_version` - إصدار Node.js
- ⏳ `test_nginx_configuration` - تكوين Nginx
- ⏳ `test_entrypoint_script` - سكريبت البداية

### 2. Nginx Configuration Tests

#### 2.1 Nginx Main Configuration
**الملف**: `frontend/nginx.conf`

**الاختبارات المطلوبة**:
- ⏳ `test_listen_port` - المنفذ 80
- ⏳ `test_root_location` - موقع الجذر
- ⏳ `test_api_proxy_pass` - proxy_pass للـ API
- ⏳ `test_authorization_header_forwarding` - تمرير Authorization header ✅ (تم الإصلاح)
- ⏳ `test_websocket_support` - دعم WebSocket
- ⏳ `test_timeout_settings` - إعدادات المهلة
- ⏳ `test_no_duplicate_directives` - عدم تكرار التوجيهات ✅ (تم الإصلاح)

**التعديلات المرتبطة**:
- إضافة `proxy_set_header Authorization $http_authorization;`
- إزالة `proxy_http_version 1.1` المكررة
- تبسيط `proxy_pass ${BACKEND_URL}`

#### 2.2 Environment Variable Substitution
**الملف**: `frontend/docker-entrypoint.sh`

**الاختبارات المطلوبة**:
- ⏳ `test_envsubst_execution` - تنفيذ envsubst
- ⏳ `test_backend_url_substitution` - استبدال BACKEND_URL
- ⏳ `test_nginx_start` - بدء Nginx

### 3. Database Tests

#### 3.1 MongoDB Connection
**الاختبارات المطلوبة**:
- ⏳ `test_mongodb_connection` - الاتصال بـ MongoDB
- ⏳ `test_database_creation` - إنشاء قاعدة البيانات
- ⏳ `test_collection_creation` - إنشاء المجموعات
- ⏳ `test_beanie_initialization` - تهيئة Beanie

#### 3.2 MongoDB Operations
**الاختبارات المطلوبة**:
- ⏳ `test_insert_document` - إدراج وثيقة
- ⏳ `test_find_document` - البحث عن وثيقة
- ⏳ `test_update_document` - تحديث وثيقة
- ⏳ `test_delete_document` - حذف وثيقة
- ⏳ `test_transaction_support` - دعم المعاملات

### 4. Redis Tests

#### 4.1 Redis Connection
**الاختبارات المطلوبة**:
- ⏳ `test_redis_connection` - الاتصال بـ Redis
- ⏳ `test_redis_ping` - اختبار ping
- ⏳ `test_connection_pool` - مجمع الاتصالات

#### 4.2 Redis Operations
**الاختبارات المطلوبة**:
- ⏳ `test_set_key` - تعيين مفتاح
- ⏳ `test_get_key` - جلب مفتاح
- ⏳ `test_delete_key` - حذف مفتاح
- ⏳ `test_key_expiration` - انتهاء صلاحية المفتاح
- ⏳ `test_rate_limiting_storage` - تخزين حد المعدل

---

## 🔗 Integration & E2E Testing Map

### 1. User Journey Tests (رحلات المستخدم)

#### 1.1 New User Journey
**السيناريو**: مستخدم جديد يسجل ويستخدم النظام

**الخطوات**:
1. ⏳ زيارة الصفحة الرئيسية
2. ⏳ النقر على "تسجيل"
3. ⏳ ملء نموذج التسجيل
4. ⏳ تسجيل دخول تلقائي
5. ⏳ إنشاء جلسة جديدة
6. ⏳ إرسال رسالة للـ AI
7. ⏳ استقبال رد من الـ AI
8. ⏳ رفع ملف
9. ⏳ تسجيل الخروج

#### 1.2 Existing User Journey
**السيناريو**: مستخدم موجود يعود للنظام

**الخطوات**:
1. ⏳ زيارة الصفحة الرئيسية
2. ⏳ النقر على "تسجيل دخول"
3. ⏳ إدخال بيانات الاعتماد
4. ⏳ عرض الجلسات السابقة
5. ⏳ فتح جلسة قديمة
6. ⏳ استكمال المحادثة
7. ⏳ تسجيل الخروج

### 2. Authentication Flow Tests

#### 2.1 Complete Authentication Flow
**الاختبارات المطلوبة**:
- ⏳ `test_e2e_register_login_logout` - دورة كاملة
- ⏳ `test_token_persistence` - استمرارية التوكن
- ⏳ `test_token_refresh_on_expiry` - تجديد عند الانتهاء
- ⏳ `test_401_handling` - معالجة 401

**التعديلات المرتبطة**:
- إصلاح Authorization header forwarding في Nginx
- إصلاح BillingMiddleware blocking

#### 2.2 Session Management Flow
**الاختبارات المطلوبة**:
- ⏳ `test_create_multiple_sessions` - إنشاء عدة جلسات
- ⏳ `test_switch_between_sessions` - التبديل بين الجلسات
- ⏳ `test_session_persistence` - استمرارية الجلسات
- ⏳ `test_session_sse_stream` - تدفق SSE

**التعديلات المرتبطة**:
- إزالة rate limiter decorators من session_routes

### 3. Frontend-Backend Integration Tests

#### 3.1 API Communication
**الاختبارات المطلوبة**:
- ⏳ `test_frontend_to_backend_auth` - مصادقة Frontend-Backend
- ⏳ `test_nginx_proxy_forwarding` - تمرير Nginx ✅ (تم الاختبار)
- ⏳ `test_cors_headers` - رؤوس CORS
- ⏳ `test_error_responses` - استجابات الأخطاء

**التحقق من الإصلاحات**:
- ✅ Nginx يمرر Authorization header
- ✅ Backend يستقبل التوكنات بشكل صحيح
- ✅ لا توجد مشاكل 401 Unauthorized

#### 3.2 SSE (Server-Sent Events) Integration
**الاختبارات المطلوبة**:
- ⏳ `test_sse_connection_establishment` - إنشاء اتصال SSE
- ⏳ `test_sse_event_reception` - استقبال أحداث SSE
- ⏳ `test_sse_reconnection` - إعادة الاتصال
- ⏳ `test_sse_error_handling` - معالجة أخطاء SSE

### 4. Security Tests

#### 4.1 XSS Protection Tests
**الاختبارات المطلوبة**:
- ⏳ `test_script_tag_sanitization` - تنظيف script tags
- ⏳ `test_event_handler_sanitization` - تنظيف event handlers
- ⏳ `test_html_injection_prevention` - منع حقن HTML
- ⏳ `test_bleach_integration` - تكامل Bleach ✅ (تم إضافته)

#### 4.2 Authentication Security Tests
**الاختبارات المطلوبة**:
- ⏳ `test_jwt_signature_validation` - التحقق من توقيع JWT
- ⏳ `test_expired_token_rejection` - رفض توكن منتهي
- ⏳ `test_invalid_token_rejection` - رفض توكن غير صحيح
- ⏳ `test_sql_injection_prevention` - منع SQL injection
- ⏳ `test_csrf_protection` - حماية CSRF

#### 4.3 Rate Limiting Tests
**الاختبارات المطلوبة**:
- ⏳ `test_rate_limit_enforcement` - تنفيذ حد المعدل
- ⏳ `test_rate_limit_per_endpoint` - حد لكل endpoint
- ⏳ `test_rate_limit_429_response` - استجابة 429
- ⏳ `test_redis_rate_limit_storage` - تخزين في Redis

**التعديلات المرتبطة**:
- إزالة rate limiter decorators من auth و session routes
- الاعتماد على global rate limiting middleware

### 5. Performance & Load Tests

#### 5.1 Load Tests
**الاختبارات المطلوبة**:
- ⏳ `test_concurrent_users` - مستخدمين متزامنين
- ⏳ `test_session_scalability` - قابلية توسع الجلسات
- ⏳ `test_database_performance` - أداء قاعدة البيانات
- ⏳ `test_redis_performance` - أداء Redis

#### 5.2 Stress Tests
**الاختبارات المطلوبة**:
- ⏳ `test_high_message_volume` - حجم رسائل عالي
- ⏳ `test_large_file_uploads` - رفع ملفات كبيرة
- ⏳ `test_memory_usage` - استخدام الذاكرة
- ⏳ `test_cpu_usage` - استخدام المعالج

---

## 📊 Priority Matrix (مصفوفة الأولويات)

### Critical (🔴 حرجة) - يجب اختبارها أولاً

| المكون | الملف | السبب | الحالة |
|--------|-------|-------|--------|
| **AuthService** | auth_service.py | تم تعديله (إزالة decorators) | ✅ اختبارات منشأة |
| **TokenService** | token_service.py | أساس المصادقة | ✅ اختبارات منشأة |
| **SessionRoutes** | session_routes.py | تم إصلاحه (401 bug) | ✅ اختبارات منشأة |
| **BillingMiddleware** | billing_middleware.py | معطل حالياً | ⚠️ يحتاج إصلاح أولاً |
| **Nginx Config** | nginx.conf | تم تعديله (Authorization) | ⏳ اختبارات مطلوبة |
| **Sanitizer** | sanitizer.py | أمان (XSS) | ⏳ اختبارات مطلوبة |

### High Priority (🟡 عالية)

| المكون | الملف | السبب | الحالة |
|--------|-------|-------|--------|
| **User Model** | user.py | 0% تغطية | ✅ اختبارات منشأة |
| **Subscription Model** | subscription.py | متعلق بـ BillingMiddleware | ✅ اختبارات منشأة |
| **FileService** | file_service.py | وظيفة أساسية | ⏳ اختبارات مطلوبة |
| **Frontend Auth** | useAuth.ts | واجهة المستخدم | ⏳ اختبارات مطلوبة |
| **SSE Integration** | useAgentStream.ts | تدفق الأحداث | ⏳ اختبارات مطلوبة |

### Medium Priority (🟠 متوسطة)

| المكون | الملف | السبب | الحالة |
|--------|-------|-------|--------|
| **Chat Components** | ChatBox.vue | واجهة المستخدم | ⏳ اختبارات مطلوبة |
| **File Components** | FilePanel.vue | وظيفة مساعدة | ⏳ اختبارات مطلوبة |
| **Utils** | time.ts, dom.ts | مساعدة | ⏳ اختبارات مطلوبة |

---

## 🎯 خطة التنفيذ الموصى بها

### المرحلة 1: الأساسيات (أسبوع 1)
**الهدف**: إصلاح الاختبارات الموجودة وتفعيلها

1. ✅ إصلاح أخطاء الاستيراد في الاختبارات الموجودة
2. ✅ تفعيل `test_token_service.py`
3. ✅ تفعيل `test_auth_service.py`
4. ✅ تفعيل `test_session_service.py`
5. ⏳ إنشاء اختبارات Nginx configuration
6. ⏳ اختبارات Docker compose

**النتيجة المتوقعة**: رفع التغطية من 20.93% إلى ~40%

### المرحلة 2: البنية التحتية (أسبوع 2)
**الهدف**: اختبار الطبقات الأساسية

1. ⏳ اختبارات MongoDB (connection, CRUD)
2. ⏳ اختبارات Redis (cache, rate limiting)
3. ⏳ اختبارات Middleware (بعد إصلاح BillingMiddleware)
4. ⏳ اختبارات Utils & Security (Sanitizer)

**النتيجة المتوقعة**: رفع التغطية إلى ~60%

### المرحلة 3: Frontend (أسبوع 3)
**الهدف**: اختبار واجهة المستخدم

1. ⏳ إعداد Vitest/Jest للـ Frontend
2. ⏳ اختبارات Components (Auth, Chat, Session)
3. ⏳ اختبارات Composables (useAuth, useAgentStream)
4. ⏳ اختبارات Utils

**النتيجة المتوقعة**: Frontend coverage >70%

### المرحلة 4: التكامل (أسبوع 4)
**الهدف**: اختبارات التكامل الكامل

1. ⏳ E2E tests مع Cypress/Playwright
2. ⏳ User journey tests
3. ⏳ Frontend-Backend integration tests
4. ⏳ SSE integration tests

**النتيجة المتوقعة**: Overall coverage >90%

### المرحلة 5: الأمان والأداء (أسبوع 5)
**الهدف**: اختبارات متقدمة

1. ⏳ Security tests (XSS, CSRF, SQL Injection)
2. ⏳ Performance tests
3. ⏳ Load tests
4. ⏳ Stress tests

**النتيجة المتوقعة**: Complete test suite

---

## 📈 مؤشرات النجاح

### Backend
- ✅ Line Coverage: >90%
- ⏳ Branch Coverage: >85%
- ⏳ Function Coverage: >90%

### Frontend
- ⏳ Component Coverage: >80%
- ⏳ Composable Coverage: >90%
- ⏳ Utils Coverage: >85%

### Integration
- ⏳ E2E Test Pass Rate: 100%
- ⏳ User Journey Coverage: 100%
- ⏳ API Integration: 100%

### Security
- ⏳ XSS Prevention: Verified
- ⏳ CSRF Protection: Verified
- ⏳ Rate Limiting: Verified
- ⏳ Authentication: Verified

---

## 🔧 الأدوات المستخدمة

### Backend Testing
- **pytest** - إطار الاختبار
- **pytest-cov** - قياس التغطية
- **pytest-asyncio** - اختبارات async
- **httpx** - HTTP client للاختبار
- **fakeredis** - Redis مزيف للاختبار
- **mongomock** - MongoDB مزيف للاختبار

### Frontend Testing
- **Vitest** - إطار الاختبار (Vue)
- **@vue/test-utils** - أدوات اختبار Vue
- **happy-dom** - DOM للاختبار
- **@testing-library/vue** - React Testing Library style
- **Cypress** - E2E testing
- **Playwright** - E2E testing alternative

### CI/CD
- **GitHub Actions** - التكامل المستمر
- **Codecov** - تقارير التغطية
- **SonarQube** - جودة الكود (اختياري)

---

## 📚 الملفات المرجعية

### التوثيق الموجود
1. ✅ `FINAL_DEPLOYMENT_REPORT_ENGLISH.md` - دليل النشر الكامل
2. ✅ `BUG_FIX_REPORT.md` - تقرير إصلاح Nginx proxy
3. ✅ `AUTHENTICATION_BUG_FIX_REPORT.md` - تقرير إصلاح المصادقة
4. ✅ `TEST_COVERAGE_PLAN.md` - خطة التغطية الأساسية
5. ✅ `TESTING_COVERAGE_REPORT.md` - تقرير التغطية التفصيلي
6. ✅ `QUICK_START_TESTING.md` - دليل البدء السريع
7. ✅ `TESTING_SUMMARY.md` - ملخص الاختبارات

### ملفات الاختبار المنشأة
1. ✅ `backend/tests/unit/test_token_service.py` (49 اختبار)
2. ✅ `backend/tests/unit/test_auth_service.py` (35+ اختبار)
3. ✅ `backend/tests/unit/test_session_service.py` (30+ اختبار)
4. ✅ `backend/tests/unit/test_middleware.py` (20+ اختبار)
5. ✅ `backend/tests/unit/test_models.py` (25+ اختبار)
6. ✅ `backend/tests/integration/test_api_routes.py` (30+ اختبار)

---

## 🎉 الخلاصة

تم إنشاء **خريطة اختبارات شاملة** تغطي:

- ✅ **Backend**: 160+ اختبار منشأ (بحاجة لتفعيل)
- ⏳ **Frontend**: ~200+ اختبار مطلوب
- ⏳ **Infrastructure**: ~50+ اختبار مطلوب
- ⏳ **Integration/E2E**: ~100+ اختبار مطلوب

**المجموع المقدر**: **500+ اختبار** لتغطية شاملة >90%

**الحالة الحالية**: 
- Backend: 20.93% → الهدف 90%
- Frontend: 0% → الهدف 80%
- Overall: ~10% → الهدف >90%

**الوقت المقدر**: 4-5 أسابيع للتنفيذ الكامل

---

**تم إنشاء الخريطة**: 26 ديسمبر 2025  
**الإصدار**: 1.0  
**المصدر**: تحليل شامل لجميع التعديلات والإصلاحات المنفذة
