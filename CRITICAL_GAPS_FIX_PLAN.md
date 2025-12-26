# خطة إصلاح الفجوات الحرجة
## Critical Gaps Fix Plan - Phase 2

**التاريخ:** 2025-12-26  
**الحالة:** خطة جاهزة للتنفيذ  
**المدة المقدرة:** 1-2 أيام للإصلاحات الحرجة  
**الأولوية:** 🔴 CRITICAL - يجب البدء فورًا

---

## 🎯 الهدف (Objective)

إصلاح الفجوات الحرجة المكتشفة في تحليل تدفق المستخدم لضمان أمان وموثوقية التطبيق.

---

## 🚨 المرحلة 1: Critical Fixes (يجب إصلاحها فورًا)

### 1. GAP-SESSION-001: Session Ownership Verification

**المشكلة:**
```python
# الكود الحالي في session_routes.py - غير آمن!
@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[List[FileInfo]]:
    if not current_user and not await agent_service.is_session_shared(session_id):
        raise UnauthorizedError()
    # ⚠️ لا يتحقق من ownership إذا كان المستخدم مسجل دخول!
    files = await agent_service.get_session_files(session_id, current_user.id if current_user else None)
    return APIResponse.success(files)
```

**الإصلاح:**
```python
# الكود المحسّن - آمن
@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[List[FileInfo]]:
    """Get session files with proper ownership verification"""
    
    if current_user:
        # Verify user owns this session
        session = await agent_service.get_session(session_id, current_user.id)
        if not session:
            raise UnauthorizedError("Session not found or access denied")
    else:
        # For non-authenticated users, check if session is shared
        if not await agent_service.is_session_shared(session_id):
            raise UnauthorizedError("This session is not publicly shared")
    
    files = await agent_service.get_session_files(session_id, current_user.id if current_user else None)
    return APIResponse.success(files)
```

**الملفات المتأثرة:**
- `backend/app/interfaces/api/session_routes.py`

**الوقت المقدر:** 30 دقيقة  
**الأولوية:** 🔴 CRITICAL

---

### 2. GAP-BILLING-002: Webhook Signature Verification

**المشكلة:**
```python
# في billing_routes.py - التحقق من Signature قد يكون ضعيفًا
@router.post("/webhook")
async def stripe_webhook(
    http_request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Missing Stripe-Signature header'
        )
    body = await http_request.body()
    # ⚠️ يجب التأكد من الـ signature verification
    result = await stripe_service.handle_webhook_event(body, stripe_signature)
    return result
```

**الإصلاح:**
```python
# في stripe_service.py
import stripe
import logging

logger = logging.getLogger(__name__)

class StripeService:
    async def handle_webhook_event(self, payload: bytes, signature: str):
        """Handle Stripe webhook with signature verification"""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, 
                signature, 
                self.settings.stripe_webhook_secret
            )
            
            logger.info(f"Valid webhook received: {event['type']}")
            
            # Process event
            if event['type'] == 'checkout.session.completed':
                await self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                await self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                await self._handle_payment_failed(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                await self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event['data']['object'])
            else:
                logger.warning(f"Unhandled webhook event type: {event['type']}")
            
            return {"status": "success", "event_type": event['type']}
            
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature - log and reject
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid webhook signature'
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to process webhook'
            )
```

**الملفات المتأثرة:**
- `backend/app/infrastructure/external/billing/stripe_service.py`
- `backend/app/interfaces/api/billing_routes.py`

**الوقت المقدر:** 45 دقيقة  
**الأولوية:** 🔴 CRITICAL

---

## 🟠 المرحلة 2: High Priority Fixes

### 3. GAP-AUTH-002: Add Logout Endpoint

**الإصلاح:**
```python
# في auth_routes.py
@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user and invalidate token
    
    This endpoint logs out the current user by revoking their access token.
    The token will be added to a blacklist to prevent further use.
    """
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Revoke token
    await auth_service.logout(token)
    
    logger.info(f"User logged out: {current_user.id}")
    
    return APIResponse.success({
        "message": "Logged out successfully"
    })
```

**Redis Token Blacklist:**
```python
# في token_service.py
import redis
from datetime import timedelta

class TokenService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def revoke_token(self, token: str) -> bool:
        """Add token to blacklist"""
        try:
            # Get token expiry
            payload = self.verify_token(token)
            if not payload:
                return False
            
            exp = payload.get("exp")
            if not exp:
                return False
            
            # Calculate TTL
            ttl = exp - int(datetime.utcnow().timestamp())
            if ttl <= 0:
                return True  # Token already expired
            
            # Add to blacklist with TTL
            self.redis.setex(
                f"blacklist:{token}",
                ttl,
                "1"
            )
            
            return True
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return self.redis.exists(f"blacklist:{token}") > 0
```

**Middleware للتحقق من Blacklist:**
```python
# في dependencies.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> User:
    """Get current authenticated user with blacklist check"""
    
    # Check if token is blacklisted
    if token_service.is_token_blacklisted(token):
        raise UnauthorizedError("Token has been revoked")
    
    # Verify token
    user = await auth_service.verify_token(token)
    if not user:
        raise UnauthorizedError("Invalid token")
    
    return user
```

**الملفات المتأثرة:**
- `backend/app/interfaces/api/auth_routes.py`
- `backend/app/application/services/token_service.py`
- `backend/app/interfaces/dependencies.py`

**الوقت المقدر:** 1 ساعة  
**الأولوية:** 🟠 HIGH

---

### 4. GAP-AUTH-003: Complete Password Reset Flow

**الإصلاح:**

#### 4.1 إضافة Verification Code Storage

```python
# في email_service.py
import secrets
import redis
from datetime import timedelta

class EmailService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    async def send_verification_code(self, email: str) -> str:
        """Send verification code via email"""
        # Generate code
        code = self.generate_verification_code()
        
        # Store in Redis with 10-minute expiry
        key = f"reset_code:{email}"
        self.redis.setex(key, timedelta(minutes=10), code)
        
        # TODO: Send actual email
        # For now, just log it (for development)
        logger.info(f"Verification code for {email}: {code}")
        
        # In production, use SendGrid/AWS SES:
        # await self.send_email(
        #     to=email,
        #     subject="Password Reset Code",
        #     body=f"Your verification code is: {code}"
        # )
        
        return code
    
    def verify_code(self, email: str, code: str) -> bool:
        """Verify reset code"""
        key = f"reset_code:{email}"
        stored_code = self.redis.get(key)
        
        if not stored_code:
            return False
        
        # Compare codes
        if stored_code.decode('utf-8') == code:
            # Delete code after successful verification
            self.redis.delete(key)
            return True
        
        return False
```

#### 4.2 تحديث Auth Routes

```python
# في auth_routes.py
@router.post("/send-verification-code")
@limiter.limit("3/hour")
async def send_verification_code(
    request: Request,
    req: SendVerificationCodeRequest,
    email_service: EmailService = Depends(get_email_service)
):
    """Send verification code for password reset"""
    try:
        # Send code
        await email_service.send_verification_code(req.email)
        
        return APIResponse.success({
            "message": "Verification code sent to your email"
        })
    except Exception as e:
        logger.error(f"Error sending verification code: {e}")
        # Don't reveal if email exists or not (security)
        return APIResponse.success({
            "message": "If the email exists, a verification code has been sent"
        })

@router.post("/reset-password")
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    req: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Reset password with verification code"""
    
    # Verify code
    if not email_service.verify_code(req.email, req.verification_code):
        raise BadRequestError("Invalid or expired verification code")
    
    # Reset password
    await auth_service.reset_password(req.email, req.new_password)
    
    return APIResponse.success({
        "message": "Password reset successfully"
    })
```

**الملفات المتأثرة:**
- `backend/app/application/services/email_service.py`
- `backend/app/interfaces/api/auth_routes.py`

**الوقت المقدر:** 1.5 ساعة  
**الأولوية:** 🟠 HIGH

---

### 5. GAP-BILLING-001: Usage Limit Enforcement in Frontend

**الإصلاح:**

```vue
<!-- في ChatPage.vue -->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useSubscription } from '@/composables/useSubscription';

const {
  subscription,
  isLimitExceeded,
  remainingRuns
} = useSubscription();

// Disable chat if limit exceeded
const canSendMessage = computed(() => {
  return subscription.value && !isLimitExceeded.value;
});

// Show warning when approaching limit
const showUsageWarning = computed(() => {
  if (!subscription.value) return false;
  const percentage = (subscription.value.monthly_agent_runs / subscription.value.monthly_agent_runs_limit) * 100;
  return percentage >= 80;
});
</script>

<template>
  <div>
    <!-- Usage Warning -->
    <div v-if="showUsageWarning" class="usage-warning">
      ⚠️ You've used {{ subscription.monthly_agent_runs }} of {{ subscription.monthly_agent_runs_limit }} runs this month.
      <router-link to="/settings/subscription">Upgrade</router-link>
    </div>
    
    <!-- Limit Exceeded Warning -->
    <div v-if="isLimitExceeded" class="usage-limit-exceeded">
      <span class="icon">🚫</span>
      <div>
        <strong>Usage Limit Reached</strong>
        <p>You've used all your agent runs for this month.</p>
        <router-link to="/settings/subscription" class="upgrade-btn">
          Upgrade Now
        </router-link>
      </div>
    </div>
    
    <!-- Chat Box -->
    <ChatBox 
      v-model="inputMessage" 
      :disabled="!canSendMessage"
      :is-running="isLoading" 
      @submit="handleSubmit"
      @stop="handleStop"
      :attachments="attachments"
    />
  </div>
</template>

<style scoped>
.usage-warning {
  padding: 12px 16px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  margin-bottom: 16px;
}

.usage-limit-exceeded {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: #fee2e2;
  border: 1px solid #ef4444;
  border-radius: 12px;
  margin-bottom: 16px;
}

.usage-limit-exceeded .icon {
  font-size: 32px;
}

.upgrade-btn {
  display: inline-block;
  margin-top: 8px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border-radius: 6px;
  font-weight: 600;
  text-decoration: none;
}
</style>
```

**التحديثات في ChatBox:**
```vue
<!-- في ChatBox.vue -->
<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  rows: number;
  isRunning: boolean;
  attachments: FileInfo[];
  disabled?: boolean;  // ✅ إضافة prop جديد
}>();

const sendEnabled = computed(() => {
  return !props.disabled && chatBoxFileListRef.value?.isAllUploaded && hasTextInput.value;
});
</script>

<template>
  <div class="pb-3 relative bg-[var(--background-gray-main)]">
    <div class="flex flex-col gap-3 rounded-[22px] ...">
      <ChatBoxFiles ref="chatBoxFileListRef" :attachments="attachments" />
      <div class="overflow-y-auto pl-4 pr-2">
        <textarea
          class="..."
          :disabled="disabled || isRunning"
          :value="modelValue"
          @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
          ...
        />
      </div>
      <footer class="flex flex-row justify-between w-full px-3">
        <button 
          v-if="!isRunning || sendEnabled"
          :disabled="!sendEnabled"
          @click="handleSubmit"
          ...
        >
          <SendIcon :disabled="!sendEnabled" />
        </button>
      </footer>
    </div>
  </div>
</template>
```

**الملفات المتأثرة:**
- `frontend/src/pages/ChatPage.vue`
- `frontend/src/components/ChatBox.vue`
- `frontend/src/composables/useSubscription.ts`

**الوقت المقدر:** 1 ساعة  
**الأولوية:** 🟠 HIGH

---

### 6. GAP-SESSION-002: SSE Rate Limiting

**الإصلاح:**

```python
# في session_routes.py
from app.infrastructure.middleware.advanced_rate_limit import get_rate_limit

@router.post("/{session_id}/chat")
@limiter.limit("20/minute")  # ✅ إضافة rate limit
async def chat(
    request: Request,
    session_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    """Chat endpoint with rate limiting"""
    
    # Verify user owns this session
    session = await agent_service.get_session(session_id, current_user.id)
    if not session:
        raise UnauthorizedError("Session not found or access denied")
    
    # Check if session is running
    if session.status == SessionStatus.RUNNING:
        raise BadRequestError("Session is already processing a request")
    
    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        async for event in agent_service.chat(
            session_id=session_id,
            user_id=current_user.id,
            message=chat_request.message,
            timestamp=datetime.fromtimestamp(chat_request.timestamp) if chat_request.timestamp else None,
            event_id=chat_request.event_id,
            attachments=chat_request.attachments
        ):
            logger.debug(f"Received event from chat: {event}")
            sse_event = await EventMapper.event_to_sse_event(event)
            logger.debug(f"Received event: {sse_event}")
            if sse_event:
                yield ServerSentEvent(
                    event=sse_event.event,
                    data=sse_event.data.model_dump_json() if sse_event.data else None
                )
    
    return EventSourceResponse(event_generator())
```

**الملفات المتأثرة:**
- `backend/app/interfaces/api/session_routes.py`

**الوقت المقدر:** 30 دقيقة  
**الأولوية:** 🟠 HIGH

---

### 7. GAP-SEC-001: XSS Protection in Message Display

**الإصلاح:**

```vue
<!-- في ChatMessage.vue -->
<script setup lang="ts">
import DOMPurify from 'dompurify';

const sanitizeHtml = (html: string) => {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'code', 'pre'],
    ALLOWED_ATTR: ['href', 'target', 'rel']
  });
};

const props = defineProps<{
  message: Message;
}>();

const displayContent = computed(() => {
  if (props.message.type === 'assistant' || props.message.type === 'user') {
    const content = (props.message.content as MessageContent).content;
    // Sanitize content before rendering
    return sanitizeHtml(content);
  }
  return '';
});
</script>

<template>
  <div class="chat-message">
    <!-- Use v-html only with sanitized content -->
    <div v-html="displayContent" />
    
    <!-- For plain text, use v-text -->
    <!-- <div v-text="displayContent" /> -->
  </div>
</template>
```

**تثبيت DOMPurify:**
```bash
cd /home/user/webapp/frontend
npm install dompurify
npm install --save-dev @types/dompurify
```

**الملفات المتأثرة:**
- `frontend/src/components/ChatMessage.vue`
- `frontend/package.json`

**الوقت المقدر:** 45 دقيقة  
**الأولوية:** 🟠 HIGH

---

## 📋 ملخص الإصلاحات (Fix Summary)

### Critical Fixes (المرحلة 1)
| ID | الإصلاح | الملفات | الوقت | الحالة |
|----|---------|---------|-------|--------|
| GAP-SESSION-001 | Session Ownership Verification | session_routes.py | 30 min | ⏳ Pending |
| GAP-BILLING-002 | Webhook Signature Verification | stripe_service.py, billing_routes.py | 45 min | ⏳ Pending |

**إجمالي الوقت:** 1 ساعة 15 دقيقة

### High Priority Fixes (المرحلة 2)
| ID | الإصلاح | الملفات | الوقت | الحالة |
|----|---------|---------|-------|--------|
| GAP-AUTH-002 | Add Logout Endpoint | auth_routes.py, token_service.py | 1 hour | ⏳ Pending |
| GAP-AUTH-003 | Complete Password Reset | email_service.py, auth_routes.py | 1.5 hours | ⏳ Pending |
| GAP-BILLING-001 | Usage Limit Enforcement | ChatPage.vue, ChatBox.vue | 1 hour | ⏳ Pending |
| GAP-SESSION-002 | SSE Rate Limiting | session_routes.py | 30 min | ⏳ Pending |
| GAP-SEC-001 | XSS Protection | ChatMessage.vue | 45 min | ⏳ Pending |

**إجمالي الوقت:** 5 ساعات 15 دقيقة

---

## 🚀 خطة التنفيذ (Execution Plan)

### اليوم 1: Critical Fixes
- ✅ 09:00-09:30: GAP-SESSION-001 (Session Ownership)
- ✅ 09:30-10:15: GAP-BILLING-002 (Webhook Verification)
- ✅ 10:15-10:30: Testing & Commit

### اليوم 2: High Priority Fixes (Part 1)
- ✅ 09:00-10:00: GAP-AUTH-002 (Logout Endpoint)
- ✅ 10:00-11:30: GAP-AUTH-003 (Password Reset)
- ✅ 11:30-12:00: Testing & Commit

### اليوم 2: High Priority Fixes (Part 2)
- ✅ 14:00-15:00: GAP-BILLING-001 (Usage Limit UI)
- ✅ 15:00-15:30: GAP-SESSION-002 (SSE Rate Limiting)
- ✅ 15:30-16:15: GAP-SEC-001 (XSS Protection)
- ✅ 16:15-16:30: Testing & Commit

---

## ✅ معايير القبول (Acceptance Criteria)

### للإصلاحات الحرجة:
- [ ] جميع Session endpoints تتحقق من ownership
- [ ] Stripe webhook يرفض signatures غير صحيحة
- [ ] Tests تمر بنجاح

### للإصلاحات عالية الأولوية:
- [ ] Logout endpoint يعمل بشكل صحيح
- [ ] Password reset flow مكتمل وآمن
- [ ] Frontend يمنع المستخدم عند الوصول للحد الأقصى
- [ ] SSE endpoints لديها rate limiting
- [ ] Message content محمي من XSS

---

## 📊 الاختبارات المطلوبة (Testing Requirements)

### Unit Tests
```python
# tests/test_session_ownership.py
async def test_session_ownership_verification():
    # Test that user can't access other user's sessions
    pass

# tests/test_webhook_signature.py
async def test_webhook_signature_verification():
    # Test that invalid signatures are rejected
    pass
```

### Integration Tests
```python
# tests/integration/test_auth_flow.py
async def test_logout_flow():
    # Test complete logout flow
    pass

async def test_password_reset_flow():
    # Test complete password reset flow
    pass
```

### Frontend Tests
```typescript
// tests/components/ChatBox.spec.ts
describe('ChatBox', () => {
  it('should disable input when usage limit exceeded', () => {
    // Test usage limit enforcement
  });
});
```

---

## 📈 التقدم والمتابعة (Progress Tracking)

### الحالة الحالية:
- ✅ التحليل: مكتمل
- ✅ خطة الإصلاح: مكتملة
- ⏳ التنفيذ: قيد الانتظار
- ⏳ الاختبار: قيد الانتظار
- ⏳ النشر: قيد الانتظار

### المتابعة:
- تحديث يومي على GitHub
- Commit بعد كل إصلاح
- PR review قبل merge إلى main

---

**الحالة:** ✅ خطة جاهزة للتنفيذ  
**الخطوة التالية:** بدء التنفيذ - المرحلة 1 (Critical Fixes)  
**التاريخ:** 2025-12-26
