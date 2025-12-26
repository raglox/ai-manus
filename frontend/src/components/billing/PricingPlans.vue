<template>
  <div class="pricing-plans">
    <h2 v-if="showTitle" class="pricing-title">Choose Your Plan</h2>
    
    <div class="plans-grid">
      <div
        v-for="plan in plans"
        :key="plan.id"
        class="plan-card"
        :class="{
          'plan-highlighted': plan.highlighted,
          'plan-current': currentPlan === plan.id
        }"
      >
        <!-- Current badge -->
        <div v-if="currentPlan === plan.id" class="current-badge">
          Current Plan
        </div>

        <!-- Popular badge -->
        <div v-else-if="plan.highlighted" class="popular-badge">
          Most Popular
        </div>

        <!-- Plan header -->
        <div class="plan-header">
          <h3 class="plan-name">{{ plan.name }}</h3>
          <div class="plan-price">
            <span v-if="plan.price !== null" class="price-amount">${{ plan.price }}</span>
            <span v-else class="price-amount">Custom</span>
            <span v-if="plan.price !== null" class="price-period">/month</span>
          </div>
        </div>

        <!-- Plan features -->
        <ul class="plan-features">
          <li v-for="(feature, index) in plan.features" :key="index" class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">{{ feature }}</span>
          </li>
        </ul>

        <!-- Plan action -->
        <button
          class="plan-button"
          :class="getPlanButtonClass(plan)"
          :disabled="isButtonDisabled(plan)"
          @click="handlePlanSelect(plan)"
        >
          {{ getPlanButtonText(plan) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { SubscriptionPlan } from '@/api/billing';

// Plan interface
interface PricingPlan {
  id: SubscriptionPlan;
  name: string;
  price: number | null;
  runs: number;
  features: string[];
  highlighted: boolean;
}

// Props
const props = withDefaults(defineProps<{
  currentPlan?: SubscriptionPlan;
  showTitle?: boolean;
}>(), {
  currentPlan: SubscriptionPlan.FREE,
  showTitle: true
});

// Emits
const emit = defineEmits<{
  selectPlan: [plan: SubscriptionPlan];
}>();

// Plans data
const plans = computed<PricingPlan[]>(() => [
  {
    id: SubscriptionPlan.FREE,
    name: 'Free',
    price: 0,
    runs: 10,
    features: [
      '10 agent runs per month',
      'Basic features',
      'Community support',
      'Limited file storage'
    ],
    highlighted: false
  },
  {
    id: SubscriptionPlan.BASIC,
    name: 'Basic',
    price: 19,
    runs: 1000,
    features: [
      '1,000 agent runs per month',
      'All basic features',
      'Priority processing',
      'Email support',
      '10GB file storage'
    ],
    highlighted: true
  },
  {
    id: SubscriptionPlan.PRO,
    name: 'Pro',
    price: 49,
    runs: 5000,
    features: [
      '5,000 agent runs per month',
      'All Pro features',
      'Advanced AI models',
      'Priority support',
      'API access',
      '100GB file storage'
    ],
    highlighted: false
  },
  {
    id: SubscriptionPlan.ENTERPRISE,
    name: 'Enterprise',
    price: null,
    runs: -1,
    features: [
      'Unlimited agent runs',
      'Custom features',
      'Dedicated support',
      'SLA guarantee',
      'Custom integrations',
      'Unlimited storage'
    ],
    highlighted: false
  }
]);

// Methods
function getPlanButtonClass(plan: PricingPlan) {
  if (props.currentPlan === plan.id) {
    return 'button-current';
  }
  if (plan.highlighted) {
    return 'button-primary';
  }
  return 'button-secondary';
}

function getPlanButtonText(plan: PricingPlan): string {
  if (props.currentPlan === plan.id) {
    return 'Current Plan';
  }
  if (plan.id === SubscriptionPlan.FREE) {
    return 'Downgrade';
  }
  if (plan.id === SubscriptionPlan.ENTERPRISE) {
    return 'Contact Sales';
  }
  return 'Upgrade';
}

function isButtonDisabled(plan: PricingPlan): boolean {
  return props.currentPlan === plan.id;
}

function handlePlanSelect(plan: PricingPlan) {
  if (!isButtonDisabled(plan)) {
    emit('selectPlan', plan.id);
  }
}
</script>

<style scoped>
.pricing-plans {
  width: 100%;
}

.pricing-title {
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin-bottom: 2rem;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.plan-card {
  position: relative;
  background: var(--bg-card, #ffffff);
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.plan-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.plan-highlighted {
  border-color: #3b82f6;
  box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2);
}

.plan-current {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
}

.current-badge {
  position: absolute;
  top: -12px;
  right: 1rem;
  background: #10b981;
  color: white;
  padding: 0.375rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.popular-badge {
  position: absolute;
  top: -12px;
  right: 1rem;
  background: #3b82f6;
  color: white;
  padding: 0.375rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.plan-header {
  text-align: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.plan-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin-bottom: 0.5rem;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.25rem;
}

.price-amount {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text-primary, #111827);
}

.price-period {
  font-size: 1rem;
  color: var(--text-secondary, #6b7280);
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 2rem 0;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0;
  color: var(--text-secondary, #374151);
}

.feature-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.feature-text {
  font-size: 0.9375rem;
  line-height: 1.5;
}

.plan-button {
  width: 100%;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  outline: none;
}

.button-primary {
  background: #3b82f6;
  color: white;
}

.button-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.button-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.button-secondary:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.button-current {
  background: #10b981;
  color: white;
  cursor: not-allowed;
  opacity: 0.7;
}

.plan-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Responsive */
@media (max-width: 768px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }

  .pricing-title {
    font-size: 1.5rem;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .plan-card {
    background: var(--bg-card-dark, #1f2937);
    border-color: var(--border-color-dark, #374151);
  }

  .plan-current {
    background: linear-gradient(135deg, #064e3b 0%, #1f2937 100%);
  }

  .plan-name {
    color: var(--text-primary-dark, #f9fafb);
  }

  .price-amount {
    color: var(--text-primary-dark, #f9fafb);
  }

  .price-period {
    color: var(--text-secondary-dark, #9ca3af);
  }

  .feature-item {
    color: var(--text-secondary-dark, #d1d5db);
  }

  .button-secondary {
    background: #374151;
    color: #e5e7eb;
    border-color: #4b5563;
  }

  .button-secondary:hover:not(:disabled) {
    background: #4b5563;
  }
}
</style>
