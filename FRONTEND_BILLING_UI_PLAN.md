# 🎨 Frontend Billing UI - خطة التنفيذ التفصيلية

**المرحلة:** Phase 5  
**التاريخ:** 2025-12-26  
**الوقت المقدر:** 2 أيام  
**الأولوية:** عالية

---

## 📊 نظرة عامة

بناء واجهة مستخدم كاملة لإدارة الاشتراكات والفوترة في Frontend (Vue 3 + TypeScript).

---

## 🎯 المكونات المطلوبة

### 1. SubscriptionSettings.vue (الصفحة الرئيسية)
**المسار:** `frontend/src/views/SubscriptionSettings.vue`  
**الوقت:** 4 ساعات

**الميزات:**
- عرض معلومات الاشتراك الحالي
- زر الترقية/التخفيض
- رابط لإدارة الاشتراك (Customer Portal)
- مؤشر الاستخدام الشهري
- معلومات الفترة التجريبية
- حالة الاشتراك (نشط/ملغي/منتهي)

**API Calls:**
- `GET /api/v1/billing/subscription` - جلب معلومات الاشتراك

**الشكل المتوقع:**
```
┌─────────────────────────────────────────────────────┐
│  ⚙️  Subscription Settings                          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Current Plan: BASIC ($19/month)                    │
│  Status: Active ✅                                   │
│  Billing Period: Dec 26, 2025 - Jan 26, 2026       │
│                                                      │
│  Usage This Month: 150 / 1,000 runs (15%)          │
│  [████░░░░░░░░░░░░░░░]                             │
│                                                      │
│  [Upgrade to PRO] [Manage Subscription]             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

### 2. PricingPlans.vue (خطط التسعير)
**المسار:** `frontend/src/components/billing/PricingPlans.vue`  
**الوقت:** 3 ساعات

**الميزات:**
- عرض 4 خطط (FREE, TRIAL, BASIC, PRO)
- تسليط الضوء على الخطة الحالية
- زر الاشتراك/الترقية لكل خطة
- مقارنة الميزات
- تصميم responsive

**الشكل المتوقع:**
```
┌──────────┬──────────┬──────────┬──────────┐
│   FREE   │  BASIC   │   PRO    │ENTERPRISE│
│          │  ⭐      │          │          │
│   $0     │   $19    │   $49    │  Custom  │
│  /month  │  /month  │  /month  │          │
│          │          │          │          │
│ 10 runs  │1000 runs │5000 runs │Unlimited │
│ Basic    │Priority  │Advanced  │Premium   │
│          │          │          │          │
│[Current] │[Upgrade] │[Upgrade] │[Contact] │
└──────────┴──────────┴──────────┴──────────┘
```

**بيانات الخطط:**
```typescript
interface PricingPlan {
  id: 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE';
  name: string;
  price: number;
  period: 'month';
  runs: number;
  features: string[];
  highlighted: boolean;
}

const plans: PricingPlan[] = [
  {
    id: 'FREE',
    name: 'Free',
    price: 0,
    period: 'month',
    runs: 10,
    features: ['10 agent runs', 'Basic features', 'Community support'],
    highlighted: false
  },
  {
    id: 'BASIC',
    name: 'Basic',
    price: 19,
    period: 'month',
    runs: 1000,
    features: ['1,000 agent runs', 'Priority processing', 'Email support'],
    highlighted: true
  },
  {
    id: 'PRO',
    name: 'Pro',
    price: 49,
    period: 'month',
    runs: 5000,
    features: ['5,000 agent runs', 'Advanced features', 'Priority support', 'API access'],
    highlighted: false
  },
  {
    id: 'ENTERPRISE',
    name: 'Enterprise',
    price: null,
    period: 'month',
    runs: -1,
    features: ['Unlimited runs', 'Custom features', 'Dedicated support', 'SLA'],
    highlighted: false
  }
];
```

---

### 3. UpgradeButton.vue (زر الترقية)
**المسار:** `frontend/src/components/billing/UpgradeButton.vue`  
**الوقت:** 2 ساعة

**الميزات:**
- زر ديناميكي حسب الخطة الحالية
- إنشاء Stripe Checkout Session
- إعادة توجيه إلى Stripe
- معالجة الأخطاء
- حالة التحميل

**API Calls:**
- `POST /api/v1/billing/create-checkout-session`

**الكود الأساسي:**
```vue
<template>
  <button
    @click="handleUpgrade"
    :disabled="loading || disabled"
    :class="buttonClasses"
  >
    <LoadingSpinner v-if="loading" />
    <span v-else>{{ buttonText }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { createCheckoutSession } from '@/services/billing';

const props = defineProps<{
  plan: 'BASIC' | 'PRO';
  currentPlan: string;
  disabled?: boolean;
}>();

const loading = ref(false);
const router = useRouter();

const buttonText = computed(() => {
  if (props.currentPlan === props.plan) return 'Current Plan';
  return `Upgrade to ${props.plan}`;
});

const handleUpgrade = async () => {
  loading.value = true;
  try {
    const response = await createCheckoutSession({
      plan: props.plan,
      success_url: `${window.location.origin}/settings/subscription?success=true`,
      cancel_url: `${window.location.origin}/settings/subscription?canceled=true`
    });
    
    // Redirect to Stripe Checkout
    window.location.href = response.checkout_url;
  } catch (error) {
    console.error('Failed to create checkout session:', error);
    alert('Failed to start upgrade process. Please try again.');
  } finally {
    loading.value = false;
  }
};
</script>
```

---

### 4. UsageIndicator.vue (مؤشر الاستخدام)
**المسار:** `frontend/src/components/billing/UsageIndicator.vue`  
**الوقت:** 2 ساعة

**الميزات:**
- شريط تقدم للاستخدام الشهري
- نسبة مئوية
- تحذير عند الاقتراب من الحد
- تحديث تلقائي

**الشكل المتوقع:**
```
Usage This Month
150 / 1,000 runs (15%)
[████░░░░░░░░░░░░░░░] 15%
✅ 850 runs remaining
```

**الكود الأساسي:**
```vue
<template>
  <div class="usage-indicator">
    <div class="usage-header">
      <h3>Usage This Month</h3>
      <span class="usage-count">{{ used }} / {{ limit }} runs</span>
    </div>
    
    <div class="progress-bar">
      <div 
        class="progress-fill"
        :style="{ width: `${percentage}%` }"
        :class="progressClass"
      ></div>
    </div>
    
    <div class="usage-footer">
      <span :class="statusClass">
        {{ statusText }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  used: number;
  limit: number;
}>();

const percentage = computed(() => {
  return Math.min(100, (props.used / props.limit) * 100);
});

const remaining = computed(() => {
  return Math.max(0, props.limit - props.used);
});

const progressClass = computed(() => {
  if (percentage.value >= 90) return 'danger';
  if (percentage.value >= 75) return 'warning';
  return 'success';
});

const statusText = computed(() => {
  if (remaining.value === 0) return '⚠️ Limit reached';
  if (percentage.value >= 90) return `⚠️ Only ${remaining.value} runs remaining`;
  return `✅ ${remaining.value} runs remaining`;
});

const statusClass = computed(() => {
  if (remaining.value === 0) return 'status-danger';
  if (percentage.value >= 90) return 'status-warning';
  return 'status-success';
});
</script>

<style scoped>
.progress-bar {
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-fill.success { background: #4caf50; }
.progress-fill.warning { background: #ff9800; }
.progress-fill.danger { background: #f44336; }
</style>
```

---

### 5. BillingHistory.vue (سجل الفواتير)
**المسار:** `frontend/src/components/billing/BillingHistory.vue`  
**الوقت:** 3 ساعات

**الميزات:**
- قائمة الفواتير السابقة
- حالة الدفع (مدفوع/معلق/فشل)
- رابط تحميل الفاتورة
- تاريخ ومبلغ كل فاتورة

**ملاحظة:** هذا المكون يحتاج إلى API endpoint إضافي للفواتير (يمكن تأجيله للمرحلة 6).

**الشكل المتوقع:**
```
┌────────────────────────────────────────────┐
│  Billing History                           │
├────────────────────────────────────────────┤
│  Date         Plan    Amount   Status      │
│  Jan 26, 2026 BASIC   $19.00   ✅ Paid    │
│  Dec 26, 2025 BASIC   $19.00   ✅ Paid    │
│  Nov 26, 2025 FREE    $0.00    -          │
└────────────────────────────────────────────┘
```

---

## 🛠️ ملفات الخدمات (Services)

### billing.service.ts
**المسار:** `frontend/src/services/billing.ts`  
**الوقت:** 1 ساعة

```typescript
import axios from 'axios';

const API_BASE = '/api/v1/billing';

export interface Subscription {
  id: string;
  user_id: string;
  plan: 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE';
  status: string;
  monthly_agent_runs: number;
  monthly_agent_runs_limit: number;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_trial: boolean;
  trial_end: string | null;
}

export interface CreateCheckoutSessionRequest {
  plan: 'BASIC' | 'PRO';
  success_url?: string;
  cancel_url?: string;
}

export interface CreateCheckoutSessionResponse {
  checkout_session_id: string;
  checkout_url: string;
}

export interface CustomerPortalResponse {
  portal_url: string;
}

// Get current subscription
export const getSubscription = async (): Promise<Subscription> => {
  const response = await axios.get<Subscription>(`${API_BASE}/subscription`);
  return response.data;
};

// Create Stripe checkout session
export const createCheckoutSession = async (
  request: CreateCheckoutSessionRequest
): Promise<CreateCheckoutSessionResponse> => {
  const response = await axios.post<CreateCheckoutSessionResponse>(
    `${API_BASE}/create-checkout-session`,
    request
  );
  return response.data;
};

// Create customer portal session
export const createPortalSession = async (): Promise<CustomerPortalResponse> => {
  const response = await axios.post<CustomerPortalResponse>(
    `${API_BASE}/create-portal-session`
  );
  return response.data;
};

// Activate trial
export const activateTrial = async (): Promise<void> => {
  await axios.post(`${API_BASE}/activate-trial`);
};
```

---

## 🗺️ التوجيه (Routing)

### إضافة المسار في Router
**الملف:** `frontend/src/router/index.ts`

```typescript
{
  path: '/settings/subscription',
  name: 'SubscriptionSettings',
  component: () => import('@/views/SubscriptionSettings.vue'),
  meta: { requiresAuth: true }
}
```

---

## 📋 قائمة المهام التفصيلية

### اليوم الأول (8 ساعات)

**الصباح (4 ساعات)**
- [ ] إنشاء `billing.service.ts` مع جميع API calls (1 ساعة)
- [ ] إنشاء `PricingPlans.vue` مع التصميم (3 ساعات)

**الظهر (4 ساعات)**
- [ ] إنشاء `UsageIndicator.vue` مع شريط التقدم (2 ساعة)
- [ ] إنشاء `UpgradeButton.vue` مع معالجة Stripe (2 ساعة)

### اليوم الثاني (8 ساعات)

**الصباح (4 ساعات)**
- [ ] إنشاء `SubscriptionSettings.vue` الصفحة الرئيسية (4 ساعات)

**الظهر (4 ساعات)**
- [ ] دمج جميع المكونات في الصفحة الرئيسية (2 ساعة)
- [ ] إضافة التوجيه والربط مع القائمة (1 ساعة)
- [ ] اختبار شامل للواجهة (1 ساعة)

---

## 🎨 التصميم والأسلوب

### نظام الألوان

```css
:root {
  /* Primary colors */
  --color-primary: #2563eb;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  
  /* Subscription plan colors */
  --plan-free: #6b7280;
  --plan-basic: #3b82f6;
  --plan-pro: #8b5cf6;
  --plan-enterprise: #f59e0b;
  
  /* Background */
  --bg-card: #ffffff;
  --bg-hover: #f3f4f6;
  
  /* Text */
  --text-primary: #111827;
  --text-secondary: #6b7280;
}
```

### مكتبة UI

استخدام المكونات الموجودة من `@/components/ui`:
- Button
- Card
- Progress
- Badge
- Modal

---

## ✅ معايير الإنجاز

- [ ] جميع المكونات الخمسة تم إنشاؤها
- [ ] ملف الخدمات يعمل مع Backend
- [ ] التصميم responsive على جميع الشاشات
- [ ] معالجة الأخطاء في جميع API calls
- [ ] حالات التحميل واضحة للمستخدم
- [ ] اختبار دورة الترقية الكاملة
- [ ] التوجيه إلى Stripe Checkout يعمل
- [ ] رابط Customer Portal يعمل
- [ ] مؤشر الاستخدام يتحدث تلقائياً

---

## 🧪 خطة الاختبار

### اختبارات يدوية

1. **عرض الاشتراك الحالي**
   - تسجيل الدخول
   - الانتقال إلى /settings/subscription
   - التحقق من عرض الخطة الحالية بشكل صحيح

2. **الترقية إلى BASIC**
   - النقر على "Upgrade to BASIC"
   - التحقق من إعادة التوجيه إلى Stripe
   - إكمال الدفع ببطاقة اختبار
   - التحقق من تحديث الخطة

3. **مؤشر الاستخدام**
   - إنشاء عدة sessions
   - التحقق من تحديث العداد
   - التحقق من تغيير اللون عند الاقتراب من الحد

4. **Customer Portal**
   - النقر على "Manage Subscription"
   - التحقق من فتح Stripe Portal
   - تغيير طريقة الدفع
   - إلغاء الاشتراك

### اختبارات آلية (اختياري)

```typescript
// Example test with Vitest
import { mount } from '@vue/test-utils';
import UsageIndicator from '@/components/billing/UsageIndicator.vue';

describe('UsageIndicator', () => {
  it('displays correct percentage', () => {
    const wrapper = mount(UsageIndicator, {
      props: { used: 500, limit: 1000 }
    });
    
    expect(wrapper.text()).toContain('50%');
    expect(wrapper.text()).toContain('500 / 1,000');
  });
  
  it('shows warning at 90%', () => {
    const wrapper = mount(UsageIndicator, {
      props: { used: 900, limit: 1000 }
    });
    
    expect(wrapper.find('.progress-fill').classes()).toContain('warning');
  });
});
```

---

## 📊 التقدم المتوقع

```
Day 1:
[████████░░░░░░░░░░░░] 40%
- billing.service.ts ✅
- PricingPlans.vue ✅
- UsageIndicator.vue ✅
- UpgradeButton.vue ✅

Day 2:
[████████████████████] 100%
- SubscriptionSettings.vue ✅
- Integration & Testing ✅
```

---

## 🎯 الناتج النهائي

بعد إنجاز هذه المرحلة، سيكون لدينا:

✅ واجهة مستخدم كاملة لإدارة الاشتراكات  
✅ تكامل سلس مع Stripe  
✅ تجربة مستخدم احترافية  
✅ دعم جميع خطط التسعير  
✅ مؤشرات استخدام واضحة  

**الحالة:** جاهز للبدء  
**الأولوية:** عالية  
**التعقيد:** متوسط

---

🚀 **هل تريد البدء في بناء Frontend Billing UI الآن؟**
