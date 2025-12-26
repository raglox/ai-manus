# 🎯 AI Manus - Comprehensive Testing Blueprint
## خريطة اختبارات شاملة بناءً على جميع التعديلات في المشروع

**تاريخ الإنشاء:** 26 ديسمبر 2025  
**الحالة الحالية:** التغطية 20.93% ← الهدف >90%  
**النطاق:** Backend + Frontend + Infrastructure + Integration + Security

---

## 📐 بنية المشروع الحالية

### 1️⃣ **Backend (Python/FastAPI)**
```
backend/
├── app/
│   ├── application/                    # [التغطية: 0-5%]
│   │   ├── services/
│   │   │   ├── auth_service.py         ⚡ P0: 0% [184 lines]
│   │   │   ├── token_service.py        ⚡ P0: 0% [124 lines]
│   │   │   ├── agent_service.py        ⚡ P0: 0% [172 lines]
│   │   │   ├── session_service.py      🟡 P1: 0% [156 lines]
│   │   │   ├── file_service.py         🟡 P1: 0% [86 lines]
│   │   │   └── email_service.py        🟠 P2: 0% [106 lines]
│   │   └── errors/
│   │       └── exceptions.py           ✅ Fixed: ConflictError → ValidationError
│   │
│   ├── domain/                         # [التغطية: 30-100%]
│   │   ├── models/                     
│   │   │   ├── user.py                 ⚡ P0: 0% [38 lines]
│   │   │   ├── subscription.py         ⚡ P0: 0% [89 lines]
│   │   │   ├── session.py              ✅ Good: 88.24%
│   │   │   ├── message.py              ✅ Perfect: 100%
│   │   │   └── file.py                 🟡 P1: 45%
│   │   │
│   │   └── services/                   # [التغطية: 32-100%]
│   │       ├── agents/
│   │       │   ├── base.py             🟡 Needs: 32.81% [86 lines]
│   │       │   ├── planner.py          🟡 Needs: 36.84% [48 lines]
│   │       │   └── execution.py        🟡 Needs: 44.29% [39 lines]
│   │       ├── tools/
│   │       │   ├── message.py          ✅ Good: 84.62%
│   │       │   ├── search.py           ✅ Good: 75%
│   │       │   ├── browser.py          ✅ Good: 72.55%
│   │       │   └── shell.py            🟡 Needs: 57.58%
│   │       └── flows/
│   │           └── plan_act.py         🟡 Needs: 68.52%
│   │
│   ├── infrastructure/                 # [التغطية: 0-100%]
│   │   ├── middleware/
│   │   │   ├── billing_middleware.py   ⚠️ DISABLED: 0% [Needs AuthMiddleware]
│   │   │   ├── rate_limit.py           ⚡ P0: 0%
│   │   │   └── cors.py                 🟡 P1: 0%
│   │   │
│   │   ├── external/
│   │   │   ├── sandbox/
│   │   │   │   ├── docker_sandbox.py   ✅ Stateful: 0% [NEW FEATURE]
│   │   │   │   └── plugins/            🟠 P2: 0%
│   │   │   ├── billing/
│   │   │   │   └── stripe_service.py   ⚡ P0: 0% [173 lines] [STRIPE API]
│   │   │   ├── cache/
│   │   │   │   └── redis_cache.py      🟡 P1: 0% [81 lines]
│   │   │   └── search/
│   │   │       ├── bing_search.py      🟠 P2: 0%
│   │   │       └── google_search.py    🟠 P2: 0%
│   │   │
│   │   └── persistence/
│   │       └── repositories/
│   │           ├── user_repo.py         ⚡ P0: 0%
│   │           └── subscription_repo.py ⚡ P0: 0%
│   │
│   └── interfaces/                     # [التغطية: 0%]
│       └── api/
│           ├── auth_routes.py          ✅ Fixed: @limiter removed
│           ├── session_routes.py       ✅ Fixed: 401 bug, @limiter removed
│           ├── billing_routes.py       ⚡ P0: 0% [Stripe Checkout]
│           └── file_routes.py          🟡 P1: 0%
│
└── main.py                             ⚡ P0: 0% [66 lines] [App Setup]
```

---

## 2️⃣ **Frontend (Vue 3 + TypeScript)**

```
frontend/
├── src/
│   ├── components/                     # [اختبارات: 0%]
│   │   ├── auth/
│   │   │   ├── LoginForm.vue           ⚡ P0: Needs tests
│   │   │   └── RegisterForm.vue        ⚡ P0: Needs tests
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatBox.vue             ⚡ P0: Needs tests
│   │   │   ├── MessageItem.vue         🟡 P1: Needs tests
│   │   │   └── InputBox.vue            🟡 P1: Needs tests
│   │   │
│   │   ├── session/
│   │   │   ├── SessionList.vue         🟡 P1: Needs tests
│   │   │   └── SessionItem.vue         🟡 P1: Needs tests
│   │   │
│   │   ├── files/
│   │   │   ├── FilePanel.vue           🟡 P1: Needs tests
│   │   │   └── FileUploader.vue        🟡 P1: Needs tests
│   │   │
│   │   ├── terminal/
│   │   │   └── ShellTerminal.vue       ✅ New Feature: WebSocket + xterm.js
│   │   │
│   │   ├── vnc/
│   │   │   └── VNCViewer.vue           ✅ New Feature: NoVNC integration
│   │   │
│   │   └── billing/
│   │       ├── SubscriptionCard.vue    ✅ New Feature: Stripe UI
│   │       └── UsageDisplay.vue        ✅ New Feature: Usage tracking
│   │
│   ├── composables/                    # [اختبارات: 0%]
│   │   ├── useAuth.ts                  ⚡ P0: Needs tests [JWT handling]
│   │   ├── useAgentStream.ts           ⚡ P0: Needs tests [SSE]
│   │   ├── useFilePanel.ts             🟡 P1: Needs tests
│   │   ├── useDialog.ts                🟠 P2: Needs tests
│   │   ├── useI18n.ts                  🟠 P2: Needs tests
│   │   ├── useSubscription.ts          ✅ New Feature: Stripe
│   │   └── useWebSocket.ts             ✅ New Feature: Socket.IO
│   │
│   ├── utils/                          # [اختبارات: 0%]
│   │   ├── auth.ts                     ⚡ P0: Needs tests [Token mgmt]
│   │   ├── time.ts                     🟠 P2: Needs tests
│   │   ├── dom.ts                      🟠 P2: Needs tests
│   │   └── fileType.ts                 🟡 P1: Needs tests
│   │
│   ├── views/                          # [اختبارات: 0%]
│   │   ├── MainChat.vue                ⚡ P0: E2E tests [Core UI]
│   │   ├── Login.vue                   ⚡ P0: E2E tests
│   │   ├── Settings.vue                🟡 P1: E2E tests
│   │   └── SubscriptionSettings.vue    ✅ New Feature: Billing UI
│   │
│   └── api/                            # [اختبارات: 0%]
│       ├── auth.ts                     ⚡ P0: Needs tests [API calls]
│       ├── session.ts                  ⚡ P0: Needs tests
│       ├── file.ts                     🟡 P1: Needs tests
│       └── billing.ts                  ✅ New Feature: Stripe API
│
└── nginx.conf                          ✅ Fixed: Authorization header
```

---

## 3️⃣ **Infrastructure & Configuration**

```
infrastructure/
├── docker/
│   ├── Dockerfile (backend)            🟡 P1: Needs tests
│   ├── Dockerfile (frontend)           🟡 P1: Needs tests
│   └── docker-compose.*.yml            🟡 P1: Needs validation tests
│
├── nginx/
│   └── nginx.conf                      ✅ Fixed:
│                                          - Authorization header forwarding
│                                          - Duplicate proxy_http_version
│                                          - Simplified proxy_pass
│
├── database/
│   ├── MongoDB                         🟡 P1: Connection tests
│   └── Redis                           🟡 P1: Cache operation tests
│
└── external_services/
    ├── Stripe API                      ⚡ P0: Mock tests [CRITICAL]
    ├── OpenAI API                      🟡 P1: Mock tests
    └── Search APIs                     🟠 P2: Mock tests
```

---

## 🔬 خطة الاختبارات الشاملة

### **Phase 1: Backend Unit Tests (Target: 50% Coverage)**

#### 1.1 Core Services ⚡ [P0 - Critical]
**Estimated Time:** 2-3 days  
**Files:** 10 files, ~1200 lines  
**Priority:** HIGHEST

```python
# ✅ Already Created (Needs Fixes):
tests/unit/test_token_service.py          # 49 tests - Fix imports
tests/unit/test_auth_service.py           # 35+ tests - Fix ConflictError
tests/unit/test_session_service.py        # 30+ tests - Fix imports

# 🆕 To Create:
tests/unit/test_agent_service.py          # ~40 tests
  ├─ Agent creation/deletion
  ├─ Message handling
  ├─ Tool execution
  ├─ Error recovery
  └─ State management

tests/unit/test_file_service.py           # ~30 tests
  ├─ File upload/download
  ├─ GridFS operations
  ├─ Size/type validation
  └─ Error handling

tests/unit/test_email_service.py          # ~25 tests
  ├─ Email sending
  ├─ Template rendering
  ├─ SMTP configuration
  └─ Error handling
```

#### 1.2 Domain Models ⚡ [P0 - Critical]
**Estimated Time:** 1 day  
**Files:** 8 files, ~400 lines

```python
# ✅ Already Created:
tests/unit/test_models.py                 # 25+ tests - Enhance

# 🆕 To Add:
User Model Tests:
  ├─ Validation (email, password)
  ├─ Serialization/deserialization
  ├─ Password hashing
  └─ Role management

Subscription Model Tests:
  ├─ Plan validation
  ├─ Usage tracking
  ├─ Quota checking
  ├─ Trial period logic
  └─ Stripe customer ID handling
```

#### 1.3 Stripe Billing ⚡ [P0 - CRITICAL $$$]
**Estimated Time:** 2 days  
**Files:** 3 files, ~350 lines  
**Critical:** Payment processing must be 100% reliable

```python
# 🆕 To Create:
tests/unit/test_stripe_service.py         # ~60 tests
  ├─ Customer creation
  ├─ Checkout session creation
  ├─ Portal session creation
  ├─ Webhook signature verification
  ├─ Webhook handlers (6 types):
  │   ├─ checkout.session.completed
  │   ├─ customer.subscription.created
  │   ├─ customer.subscription.updated
  │   ├─ customer.subscription.deleted
  │   ├─ invoice.payment_succeeded
  │   └─ invoice.payment_failed
  ├─ Error handling
  └─ Retry logic

tests/integration/test_billing_api.py     # ~40 tests
  ├─ POST /billing/create-checkout-session
  ├─ POST /billing/create-portal-session
  ├─ GET /billing/subscription
  ├─ POST /billing/webhook (all 6 events)
  ├─ POST /billing/activate-trial
  └─ Usage limit enforcement
```

#### 1.4 Middleware 🟡 [P1 - High]
**Estimated Time:** 1 day  
**Files:** 4 files, ~250 lines

```python
# ✅ Already Created (Needs Fixes):
tests/unit/test_middleware.py             # 20+ tests

# 🆕 To Add:
BillingMiddleware Tests:
  ├─ Subscription validation
  ├─ Usage increment
  ├─ Quota enforcement
  ├─ HTTP 402 responses
  └─ Exempt endpoints (auth, health)

# ⚠️ TO CREATE FIRST:
tests/unit/test_auth_middleware.py        # ~30 tests [NEW]
  ├─ Token extraction from header
  ├─ Token validation
  ├─ request.state.user_id setting
  ├─ Invalid token handling
  ├─ Expired token handling
  └─ Missing token handling

RateLimitMiddleware Tests:
  ├─ Redis connection
  ├─ Rate limit enforcement
  ├─ IP-based limiting
  ├─ User-based limiting
  └─ Limit reset logic
```

#### 1.5 Repositories 🟡 [P1 - High]
**Estimated Time:** 1-2 days  
**Files:** 5 files, ~400 lines

```python
# 🆕 To Create:
tests/unit/test_user_repository.py        # ~35 tests
  ├─ CRUD operations (Mock MongoDB)
  ├─ Beanie query tests
  ├─ Error handling
  └─ Transaction tests

tests/unit/test_subscription_repository.py # ~35 tests
  ├─ Subscription CRUD
  ├─ Usage tracking updates
  ├─ Quota queries
  └─ Trial activation

tests/unit/test_session_repository.py     # ~30 tests
tests/unit/test_file_repository.py        # ~25 tests
```

---

### **Phase 2: Backend Integration Tests (Target: 70% Coverage)**

#### 2.1 API Routes Testing ⚡ [P0]
**Estimated Time:** 2-3 days  
**Files:** 8 routes files

```python
# ✅ Already Created (Needs Fixes):
tests/integration/test_api_routes.py      # 30+ tests

# 🔧 To Fix:
tests/test_auth_routes.py                 # Fix: BASE_URL import
tests/test_api_file.py                    # Fix: BASE_URL import

# 🆕 To Enhance:
Auth API Tests:
  ✅ POST /auth/register
  ✅ POST /auth/login
  ✅ POST /auth/refresh
  ✅ POST /auth/logout
  🆕 GET /auth/status
  🆕 POST /auth/change-password

Session API Tests:
  ✅ PUT /sessions (create)
  ✅ GET /sessions (list)
  ✅ POST /sessions (SSE stream)
  🆕 GET /sessions/{id}
  🆕 DELETE /sessions/{id}
  🆕 POST /sessions/{id}/stop
  🆕 PUT /sessions/{id}/share

Billing API Tests: [⚡ CRITICAL]
  🆕 POST /billing/create-checkout-session
  🆕 POST /billing/create-portal-session
  🆕 GET /billing/subscription
  🆕 POST /billing/webhook
  🆕 POST /billing/activate-trial

File API Tests:
  🆕 POST /files/upload
  🆕 GET /files
  🆕 GET /files/{id}
  🆕 DELETE /files/{id}
```

#### 2.2 Stateful Sandbox Testing ✅ [P0 - NEW FEATURE]
**Estimated Time:** 2 days  
**Files:** `docker_sandbox.py` (600+ lines)

```python
# 🆕 To Create:
tests/integration/test_stateful_sandbox.py # ~50 tests
  ├─ ENV persistence tests:
  │   ├─ export VAR=value
  │   ├─ Multiple exports
  │   ├─ Variable override
  │   └─ Cross-session isolation
  │
  ├─ CWD persistence tests:
  │   ├─ cd /path/to/dir
  │   ├─ Nested cd commands
  │   ├─ Relative paths
  │   └─ Invalid paths handling
  │
  ├─ Background process tests:
  │   ├─ Start process with &
  │   ├─ Multiple background jobs
  │   ├─ PID tracking
  │   ├─ Process logs retrieval
  │   ├─ Process killing
  │   └─ Process status checking
  │
  ├─ Plugin injection tests:
  │   ├─ MCP plugin loading
  │   ├─ File editor plugin
  │   └─ Custom tools injection
  │
  └─ Session isolation tests:
      ├─ Multiple sessions
      ├─ Independent state
      └─ No cross-contamination
```

#### 2.3 Database Integration 🟡 [P1]
**Estimated Time:** 1 day

```python
# 🆕 To Create:
tests/integration/test_mongodb_integration.py
  ├─ Connection pooling
  ├─ Transaction tests
  ├─ Beanie models CRUD
  └─ Error recovery

tests/integration/test_redis_integration.py
  ├─ Cache operations
  ├─ Rate limiting storage
  ├─ Session storage
  └─ Connection failover
```

---

### **Phase 3: Frontend Tests (Target: 75% Coverage)**

#### 3.1 Component Tests ⚡ [P0]
**Estimated Time:** 3-4 days  
**Framework:** Vitest + Vue Test Utils

```typescript
// 🆕 Setup Required:
// 1. Install Vitest: npm install -D vitest @vue/test-utils happy-dom
// 2. Configure vite.config.ts for tests
// 3. Create test setup file

// Auth Components [P0]:
tests/unit/LoginForm.spec.ts              // ~20 tests
  ├─ Form validation
  ├─ Login API call
  ├─ Token storage
  ├─ Error handling
  └─ Redirect after login

tests/unit/RegisterForm.spec.ts           // ~20 tests
  ├─ Form validation
  ├─ Password strength
  ├─ Register API call
  └─ Success/error states

// Chat Components [P0]:
tests/unit/ChatBox.spec.ts                // ~25 tests
  ├─ Message rendering
  ├─ SSE connection
  ├─ Streaming messages
  ├─ Message history
  └─ Scroll behavior

tests/unit/InputBox.spec.ts               // ~15 tests
  ├─ Message input
  ├─ File attachment
  ├─ Send button state
  └─ Keyboard shortcuts

// Billing Components [P0 - NEW]:
tests/unit/SubscriptionCard.spec.ts       // ~20 tests
  ├─ Plan display
  ├─ Upgrade button
  ├─ Stripe checkout
  └─ Usage display

tests/unit/UsageDisplay.spec.ts           // ~15 tests
  ├─ Usage percentage
  ├─ Quota display
  ├─ Warning states
  └─ Real-time updates

// Terminal Components [P0 - NEW]:
tests/unit/ShellTerminal.spec.ts          // ~20 tests
  ├─ xterm.js initialization
  ├─ WebSocket connection
  ├─ Command execution
  ├─ ANSI rendering
  └─ Copy/paste

// VNC Components [P0 - NEW]:
tests/unit/VNCViewer.spec.ts              // ~15 tests
  ├─ NoVNC initialization
  ├─ Connection handling
  ├─ Mouse/keyboard events
  └─ Disconnect handling
```

#### 3.2 Composables Tests 🟡 [P1]
**Estimated Time:** 2 days

```typescript
// 🆕 To Create:
tests/unit/useAuth.spec.ts                // ~30 tests
  ├─ Login/logout
  ├─ Token refresh
  ├─ isAuthenticated state
  └─ Auto-refresh logic

tests/unit/useAgentStream.spec.ts         // ~25 tests
  ├─ SSE connection
  ├─ Event parsing
  ├─ Error handling
  └─ Reconnection

tests/unit/useSubscription.spec.ts        // ~20 tests [NEW]
  ├─ Subscription status
  ├─ Usage tracking
  ├─ Upgrade flow
  └─ Portal access

tests/unit/useWebSocket.spec.ts           // ~20 tests [NEW]
  ├─ Socket.IO connection
  ├─ Event handlers
  ├─ Reconnection logic
  └─ Room management
```

#### 3.3 Utils Tests 🟡 [P1]
**Estimated Time:** 1 day

```typescript
// 🆕 To Create:
tests/unit/auth.spec.ts                   // ~20 tests
  ├─ Token storage
  ├─ Token parsing
  ├─ Expiration checking
  └─ Refresh logic

tests/unit/time.spec.ts                   // ~10 tests
tests/unit/dom.spec.ts                    // ~10 tests
tests/unit/fileType.spec.ts               // ~15 tests
```

---

### **Phase 4: End-to-End Tests (Target: 85% Coverage)**

#### 4.1 Critical User Flows ⚡ [P0]
**Estimated Time:** 3-4 days  
**Framework:** Cypress / Playwright

```typescript
// 🆕 To Create:
tests/e2e/user-journey.spec.ts            // ~15 flows

// Flow 1: New User Registration & Trial [⚡ CRITICAL]
describe('New User Journey', () => {
  it('Complete signup to first chat', () => {
    // 1. Visit homepage
    // 2. Click "Sign Up"
    // 3. Fill registration form
    // 4. Submit
    // 5. Verify email (skip in test)
    // 6. Auto-activate 14-day trial
    // 7. Redirect to dashboard
    // 8. Create first session
    // 9. Send first message
    // 10. Verify response
  })
})

// Flow 2: Existing User Login [⚡ CRITICAL]
describe('Returning User', () => {
  it('Login and continue session', () => {
    // 1. Visit /login
    // 2. Enter credentials
    // 3. Submit
    // 4. Verify JWT stored
    // 5. See session list
    // 6. Click on session
    // 7. Continue chat
  })
})

// Flow 3: Subscription Upgrade [⚡ CRITICAL $$$]
describe('Upgrade Subscription', () => {
  it('User upgrades to PRO plan', () => {
    // 1. Login
    // 2. Go to Settings
    // 3. Click "Upgrade to PRO"
    // 4. Redirect to Stripe Checkout
    // 5. Fill payment (test mode)
    // 6. Complete payment
    // 7. Webhook received
    // 8. Subscription updated
    // 9. User sees PRO features
  })
})

// Flow 4: Usage Quota Exceeded [⚡ CRITICAL]
describe('Quota Enforcement', () => {
  it('User hits usage limit', () => {
    // 1. Login as FREE user
    // 2. Make 10 requests (limit)
    // 3. 11th request → HTTP 402
    // 4. See "Upgrade" prompt
    // 5. Click upgrade
    // 6. Go to checkout
  })
})

// Flow 5: File Upload & Download [🟡 HIGH]
describe('File Management', () => {
  it('Upload, view, and download file', () => {
    // 1. Login
    // 2. Create session
    // 3. Click "Upload File"
    // 4. Select file
    // 5. Upload
    // 6. See file in panel
    // 7. Click download
    // 8. Verify file content
  })
})

// Flow 6: Terminal Interaction [🟡 HIGH - NEW]
describe('Terminal Usage', () => {
  it('Execute shell commands', () => {
    // 1. Login
    // 2. Open terminal
    // 3. Type: ls -la
    // 4. See output
    // 5. Type: cd /tmp
    // 6. Type: pwd
    // 7. Verify /tmp
  })
})

// Flow 7: VNC Browser Interaction [🟡 HIGH - NEW]
describe('VNC Browser', () => {
  it('Use browser via VNC', () => {
    // 1. Login
    // 2. Agent uses browser tool
    // 3. VNC viewer appears
    // 4. See browser screen
    // 5. Interact with mouse
    // 6. Close VNC
  })
})

// Flow 8: Real-time Dashboard [🟡 HIGH - NEW]
describe('Real-time Updates', () => {
  it('See live agent thoughts', () => {
    // 1. Login
    // 2. Send message
    // 3. WebSocket connects
    // 4. See "Thinking..." status
    // 5. See tool usage events
    // 6. See completion event
  })
})
```

#### 4.2 Security Tests ⚡ [P0]
**Estimated Time:** 2 days

```typescript
// 🆕 To Create:
tests/security/xss-protection.spec.ts     // ~15 tests
  ├─ Script injection in messages
  ├─ HTML injection
  ├─ Bleach sanitization
  └─ Output encoding

tests/security/csrf-protection.spec.ts    // ~10 tests
  ├─ CSRF token validation
  ├─ Origin checking
  └─ Same-site cookies

tests/security/jwt-security.spec.ts       // ~20 tests
  ├─ Token expiration
  ├─ Token tampering
  ├─ Signature validation
  ├─ Refresh token security
  └─ Token revocation
```

---

### **Phase 5: Performance & Load Tests (Target: 90% Coverage)**

#### 5.1 Performance Tests 🟡 [P1]
**Estimated Time:** 2 days  
**Framework:** Locust / k6

```python
# 🆕 To Create:
tests/performance/load_test.py            # Locust scenarios

# Scenario 1: Normal Load
class NormalUserBehavior(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def send_message(self):
        # Send chat message
        pass
    
    @task(2)
    def list_sessions(self):
        # Get sessions
        pass
    
    @task(1)
    def upload_file(self):
        # Upload file
        pass

# Metrics to Track:
  ├─ Response time (p50, p95, p99)
  ├─ Throughput (requests/sec)
  ├─ Error rate
  ├─ CPU/Memory usage
  └─ Database connections

# Load Profiles:
  ├─ Light: 10 concurrent users
  ├─ Medium: 50 concurrent users
  ├─ Heavy: 100 concurrent users
  └─ Spike: 0→200→0 users
```

#### 5.2 Stress Tests 🟠 [P2]
**Estimated Time:** 1 day

```python
# 🆕 To Create:
tests/stress/breaking_point.py

# Test Scenarios:
  ├─ Database connection exhaustion
  ├─ Redis connection pool limits
  ├─ Docker container limits
  ├─ Memory leaks
  └─ CPU saturation
```

---

## 📊 Summary: Total Test Count Estimate

### Backend Tests
| Category | Files | Tests | Priority | Est. Time |
|----------|-------|-------|----------|-----------|
| Core Services | 6 | ~200 | ⚡ P0 | 3 days |
| Domain Models | 8 | ~150 | ⚡ P0 | 1 day |
| Stripe Billing | 2 | ~100 | ⚡ P0 | 2 days |
| Middleware | 4 | ~80 | 🟡 P1 | 1 day |
| Repositories | 5 | ~125 | 🟡 P1 | 2 days |
| API Routes | 8 | ~150 | ⚡ P0 | 3 days |
| Stateful Sandbox | 1 | ~50 | ⚡ P0 | 2 days |
| Database Integration | 2 | ~40 | 🟡 P1 | 1 day |
| **Subtotal** | **36** | **~895** | - | **15 days** |

### Frontend Tests
| Category | Files | Tests | Priority | Est. Time |
|----------|-------|-------|----------|-----------|
| Components | 10 | ~165 | ⚡ P0 | 4 days |
| Composables | 6 | ~115 | 🟡 P1 | 2 days |
| Utils | 4 | ~55 | 🟡 P1 | 1 day |
| **Subtotal** | **20** | **~335** | - | **7 days** |

### Integration & E2E Tests
| Category | Files | Tests | Priority | Est. Time |
|----------|-------|-------|----------|-----------|
| E2E User Flows | 1 | ~60 | ⚡ P0 | 4 days |
| Security Tests | 3 | ~45 | ⚡ P0 | 2 days |
| Performance Tests | 2 | ~20 | 🟡 P1 | 3 days |
| **Subtotal** | **6** | **~125** | - | **9 days** |

### **GRAND TOTAL**
- **Files:** 62 test files
- **Tests:** ~1,355 test cases
- **Time:** ~31 working days (6 weeks)
- **Current:** 160 tests (20.93%)
- **Gap:** 1,195 tests needed

---

## 🎯 Recommended Execution Strategy

### Week 1: Fix & Foundation [Days 1-5]
**Goal:** Enable existing tests + Core services → 40%

```bash
Day 1: Fix Import Errors
  ├─ Update exception imports
  ├─ Fix BASE_URL in conftest
  ├─ Install pytest-asyncio
  └─ Run existing 160 tests

Day 2-3: Core Services Tests
  ├─ Fix token_service tests
  ├─ Fix auth_service tests
  ├─ Add agent_service tests
  └─ Add file_service tests

Day 4-5: Stripe Billing Tests [CRITICAL]
  ├─ Mock Stripe API
  ├─ Test all webhook handlers
  ├─ Test checkout flow
  └─ Test usage enforcement
```

### Week 2: Domain & Middleware [Days 6-10]
**Goal:** Models + Middleware → 60%

```bash
Day 6-7: Domain Models
  ├─ User model tests
  ├─ Subscription model tests
  └─ Session model tests

Day 8-9: Middleware
  ├─ Create AuthenticationMiddleware [NEW]
  ├─ Test BillingMiddleware
  ├─ Test RateLimitMiddleware
  └─ Re-enable BillingMiddleware

Day 10: Repositories
  ├─ User repository tests
  └─ Subscription repository tests
```

### Week 3: Integration & Stateful [Days 11-15]
**Goal:** API + Sandbox → 75%

```bash
Day 11-12: API Integration Tests
  ├─ Fix existing auth_routes tests
  ├─ Enhance session_routes tests
  ├─ Add billing_routes tests
  └─ Add file_routes tests

Day 13-15: Stateful Sandbox Tests [NEW FEATURE]
  ├─ ENV persistence tests
  ├─ CWD persistence tests
  ├─ Background process tests
  └─ Plugin injection tests
```

### Week 4: Frontend Foundation [Days 16-20]
**Goal:** Frontend Components → 80%

```bash
Day 16: Setup Vitest
  ├─ Install dependencies
  ├─ Configure vite.config.ts
  └─ Create test setup

Day 17-18: Auth & Chat Components
  ├─ LoginForm tests
  ├─ RegisterForm tests
  ├─ ChatBox tests
  └─ InputBox tests

Day 19-20: New Features [Billing, Terminal, VNC]
  ├─ SubscriptionCard tests
  ├─ ShellTerminal tests
  └─ VNCViewer tests
```

### Week 5: Frontend Complete [Days 21-25]
**Goal:** Composables + Utils → 85%

```bash
Day 21-22: Composables
  ├─ useAuth tests
  ├─ useAgentStream tests
  ├─ useSubscription tests
  └─ useWebSocket tests

Day 23: Utils
  ├─ auth.ts tests
  ├─ time.ts tests
  └─ fileType.ts tests

Day 24-25: API Client Tests
  ├─ auth.ts API client
  ├─ session.ts API client
  └─ billing.ts API client
```

### Week 6: E2E & Performance [Days 26-31]
**Goal:** Full Coverage → >90%

```bash
Day 26: Setup Cypress/Playwright
  ├─ Install Cypress
  ├─ Configure E2E tests
  └─ Create test fixtures

Day 27-28: Critical User Flows
  ├─ Registration & trial flow
  ├─ Login & chat flow
  ├─ Subscription upgrade flow [STRIPE]
  └─ Quota enforcement flow

Day 29-30: Security & Performance
  ├─ XSS protection tests
  ├─ JWT security tests
  ├─ Load tests (Locust)
  └─ Stress tests

Day 31: Final Report & Gaps
  ├─ Generate coverage report
  ├─ Identify remaining gaps
  ├─ Fill critical gaps
  └─ Final validation: >90%
```

---

## 🚨 Critical Blockers to Fix First

### 1. Import Errors [⚡ URGENT]
```bash
# Error: ConflictError not found
# Fix: Replace with ValidationError or BadRequestError

# Files to fix:
- tests/unit/test_auth_service.py
- tests/unit/test_middleware.py
- tests/unit/test_session_service.py
```

### 2. Missing BASE_URL [⚡ URGENT]
```bash
# Error: cannot import name 'BASE_URL' from 'conftest'
# Fix: Add to tests/conftest.py

# Add this:
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
```

### 3. Async Test Configuration [⚡ URGENT]
```bash
# Error: async def functions are not natively supported
# Fix: Ensure pytest-asyncio is configured

# Install:
pip install pytest-asyncio

# Verify pytest.ini:
[pytest]
asyncio_mode = auto
```

### 4. Create AuthenticationMiddleware [⚡ CRITICAL]
```python
# File: backend/app/infrastructure/middleware/auth_middleware.py
# Purpose: Extract user_id from JWT and set request.state.user_id
# Reason: BillingMiddleware depends on this

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user_info = token_service.get_user_from_token(token)
                if user_info:
                    request.state.user_id = user_info["id"]
            except Exception as e:
                logger.warning(f"Failed to extract user: {e}")
        
        return await call_next(request)

# Then in main.py:
app.add_middleware(AuthenticationMiddleware)  # BEFORE
app.add_middleware(BillingMiddleware, ...)    # AFTER
```

---

## 📈 Coverage Milestones

```
Current:    20.93% ████░░░░░░░░░░░░░░░░ [Day 0]
            ▼
Blocker Fix: 22% █████░░░░░░░░░░░░░░░ [Day 1]
            ▼
Phase 1:    40% ████████░░░░░░░░░░░░ [Week 1]
            ▼
Phase 2:    60% ████████████░░░░░░░░ [Week 2]
            ▼
Phase 3:    75% ███████████████░░░░░ [Week 3]
            ▼
Phase 4:    85% █████████████████░░░ [Week 5]
            ▼
Phase 5:    92% ██████████████████░░ [Week 6]
            ▼
Target:    >90% ██████████████████░░ ✅ ACHIEVED
```

---

## 🎉 Expected Outcomes

### After 6 Weeks:
✅ **Coverage:** >90% (from 20.93%)  
✅ **Tests:** 1,355+ test cases (from 160)  
✅ **Confidence:** Production-ready quality  
✅ **CI/CD:** Automated testing pipeline  
✅ **Documentation:** Complete test guides  
✅ **Maintenance:** Easy to add new tests

### Quality Metrics:
- **Reliability:** 99.9% uptime
- **Bug Detection:** <1% escape rate
- **Test Speed:** <5 minutes full suite
- **Coverage:** >90% enforced in CI

---

## 📚 Testing Documentation Created

| File | Purpose | Status |
|------|---------|--------|
| `TEST_COVERAGE_PLAN.md` | Detailed improvement roadmap | ✅ Created |
| `TESTING_COVERAGE_REPORT.md` | Current state analysis | ✅ Created |
| `QUICK_START_TESTING.md` | Quick test commands | ✅ Created |
| `TESTING_SUMMARY.md` | Executive summary | ✅ Created |
| `TESTING_ARCHITECTURE_DIAGRAM.md` | Visual architecture | ✅ Created |
| `COMPREHENSIVE_TESTING_BLUEPRINT.md` | This document | ✅ Created |

---

## 🔗 Critical Dependencies

### Backend:
```bash
pytest>=8.0.0
pytest-cov>=5.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.14.0
httpx>=0.27.0          # For API testing
faker>=24.0.0          # For test data
freezegun>=1.5.0       # For time mocking
```

### Frontend:
```bash
vitest>=1.0.0
@vue/test-utils>=2.4.0
happy-dom>=13.0.0
cypress>=13.0.0        # For E2E
@testing-library/vue>=8.0.0
```

### Performance:
```bash
locust>=2.20.0         # Load testing
k6>=0.48.0            # Alternative load testing
pytest-benchmark>=4.0.0
```

---

## 🎯 Success Criteria

### ✅ Coverage Target:
- [x] Infrastructure setup (100%)
- [ ] Backend unit tests (>90%)
- [ ] Backend integration (>85%)
- [ ] Frontend components (>80%)
- [ ] Frontend composables (>85%)
- [ ] E2E critical flows (100%)
- [ ] Overall: **>90%**

### ✅ Quality Target:
- [ ] All tests passing (100%)
- [ ] No import errors
- [ ] No configuration issues
- [ ] Fast test execution (<5 min)
- [ ] CI/CD integrated
- [ ] Documentation complete

### ✅ Business Critical:
- [ ] Stripe billing: 100% tested ⚡
- [ ] Authentication: 100% tested ⚡
- [ ] Session management: 100% tested ⚡
- [ ] Security: Penetration tested ⚡

---

**Blueprint Version:** 1.0  
**Last Updated:** December 26, 2025  
**Next Review:** Daily during execution  
**Owner:** Testing Team

---

## 📞 Quick Commands

```bash
# Run all tests
cd /home/root/webapp/backend
docker exec webapp-backend-1 bash -c "cd /app && pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing"

# Run specific category
docker exec webapp-backend-1 bash -c "cd /app && pytest tests/unit/ -v"
docker exec webapp-backend-1 bash -c "cd /app && pytest tests/integration/ -v"

# View coverage report
docker exec webapp-backend-1 bash -c "cd /app && python -m http.server 9000 --directory htmlcov"
# Open: http://172.245.232.188:9000

# Run comprehensive test script
docker exec webapp-backend-1 bash -c "cd /app && bash run_comprehensive_tests.sh"
```

---

**🎯 GOAL:** From 20.93% → >90% Coverage in 6 weeks  
**🚀 STATUS:** Roadmap Complete - Ready to Execute  
**⚡ PRIORITY:** Start with P0 (Critical) items immediately
