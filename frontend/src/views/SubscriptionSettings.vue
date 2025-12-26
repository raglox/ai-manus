<template>
  <div class="subscription-settings">
    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header">
        <h1 class="settings-title">Subscription & Billing</h1>
        <p class="settings-description">
          Manage your subscription plan and view usage statistics
        </p>
      </div>

      <!-- Loading state -->
      <div v-if="loading && !subscription" class="loading-state">
        <div class="spinner"></div>
        <p>Loading subscription information...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Failed to load subscription</h3>
        <p>{{ error.message }}</p>
        <button @click="refresh" class="retry-button">Try Again</button>
      </div>

      <!-- Success messages -->
      <div v-if="showSuccessMessage" class="success-message">
        <span class="success-icon">✓</span>
        Subscription updated successfully!
      </div>

      <div v-if="showCancelMessage" class="info-message">
        <span class="info-icon">ℹ️</span>
        Checkout canceled. You can try again anytime.
      </div>

      <!-- Content -->
      <div v-if="subscription" class="settings-content">
        <!-- Current Plan Card -->
        <div class="plan-card">
          <div class="card-header">
            <h2 class="card-title">Current Plan</h2>
            <span 
              class="status-badge"
              :class="`status-${statusColor}`"
            >
              {{ statusText }}
            </span>
          </div>

          <div class="plan-info">
            <div class="plan-name-section">
              <div class="plan-icon">
                <span v-if="subscription.plan === 'FREE'">🆓</span>
                <span v-else-if="subscription.plan === 'BASIC'">⭐</span>
                <span v-else-if="subscription.plan === 'PRO'">🚀</span>
                <span v-else>💼</span>
              </div>
              <div>
                <h3 class="plan-name">{{ planName }}</h3>
                <p v-if="planPrice !== null" class="plan-price">${{ planPrice }}/month</p>
                <p v-else class="plan-price">Custom Pricing</p>
              </div>
            </div>

            <!-- Trial info -->
            <div v-if="subscription.is_trial && trialDaysLeft !== null" class="trial-info">
              <span class="trial-icon">🎉</span>
              <span class="trial-text">
                Trial: {{ trialDaysLeft }} days remaining
              </span>
            </div>

            <!-- Billing period -->
            <div v-if="formattedPeriodEnd" class="billing-period">
              <span class="period-label">Current period ends:</span>
              <span class="period-date">{{ formattedPeriodEnd }}</span>
            </div>

            <!-- Cancel info -->
            <div v-if="subscription.cancel_at_period_end" class="cancel-info">
              ⚠️ Your subscription will be canceled at the end of the billing period
            </div>

            <!-- Past Due Warning -->
            <div v-if="subscription.status === 'PAST_DUE'" class="past-due-warning">
              ⚠️ Payment Failed - Please update your payment method to continue service
            </div>
          </div>

          <div class="plan-actions">
            <button
              v-if="subscription.plan === 'FREE' && !subscription.is_trial"
              @click="handleStartTrial"
              :disabled="loading"
              class="action-button button-trial"
            >
              Start 14-Day Trial
            </button>

            <button
              v-if="subscription.plan !== 'PRO'"
              @click="openManageSubscription"
              :disabled="loading"
              class="action-button button-primary"
            >
              {{ subscription.plan === 'FREE' ? 'Upgrade Plan' : 'Change Plan' }}
            </button>

            <button
              v-if="subscription.plan !== 'FREE' && subscription.stripe_customer_id"
              @click="openCustomerPortal"
              :disabled="loading"
              class="action-button button-secondary"
            >
              Manage Billing
            </button>
          </div>
        </div>

        <!-- Usage Card -->
        <div class="usage-card">
          <UsageIndicator
            :used="subscription.monthly_agent_runs"
            :limit="subscription.monthly_agent_runs_limit"
            title="Usage This Month"
          />

          <!-- Usage warning -->
          <div v-if="isLimitExceeded" class="usage-warning warning-danger">
            <span class="warning-icon">🚫</span>
            <div class="warning-content">
              <strong>Limit Reached</strong>
              <p>You've used all your agent runs for this month. Upgrade to continue.</p>
            </div>
          </div>

          <div v-else-if="isApproaching" class="usage-warning warning-caution">
            <span class="warning-icon">⚠️</span>
            <div class="warning-content">
              <strong>Approaching Limit</strong>
              <p>You're running low on agent runs. Consider upgrading your plan.</p>
            </div>
          </div>
        </div>

        <!-- Pricing Plans -->
        <div v-if="showPricingPlans" class="pricing-section">
          <PricingPlans
            :current-plan="subscription.plan"
            @select-plan="handlePlanSelect"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSubscription } from '@/composables/useSubscription';
import { SubscriptionPlan } from '@/api/billing';
import UsageIndicator from '@/components/billing/UsageIndicator.vue';
import PricingPlans from '@/components/billing/PricingPlans.vue';

// Composables
const route = useRoute();
const {
  subscription,
  loading,
  error,
  remainingRuns,
  usagePercentage,
  isApproaching,
  isLimitExceeded,
  planName,
  planPrice,
  statusColor,
  statusText,
  trialDaysLeft,
  formattedPeriodEnd,
  upgradeSubscription,
  openCustomerPortal,
  startTrial,
  refresh
} = useSubscription();

// Local state
const showSuccessMessage = ref(false);
const showCancelMessage = ref(false);
const showPricingPlans = ref(false);

// Check URL parameters
onMounted(() => {
  if (route.query.success === 'true') {
    showSuccessMessage.value = true;
    setTimeout(() => {
      showSuccessMessage.value = false;
    }, 5000);
    // Refresh subscription data
    refresh();
  }

  if (route.query.canceled === 'true') {
    showCancelMessage.value = true;
    setTimeout(() => {
      showCancelMessage.value = false;
    }, 5000);
  }
});

// Methods
function openManageSubscription() {
  showPricingPlans.value = !showPricingPlans.value;
}

async function handlePlanSelect(plan: SubscriptionPlan) {
  if (plan === SubscriptionPlan.BASIC || plan === SubscriptionPlan.PRO) {
    try {
      await upgradeSubscription(plan);
    } catch (err) {
      console.error('Failed to upgrade:', err);
      alert('Failed to start upgrade process. Please try again.');
    }
  } else if (plan === SubscriptionPlan.ENTERPRISE) {
    // Redirect to contact sales
    window.open('mailto:sales@ai-manus.com?subject=Enterprise Plan Inquiry', '_blank');
  }
}

async function handleStartTrial() {
  try {
    await startTrial();
    alert('Trial activated! You now have 50 runs for 14 days.');
  } catch (err: any) {
    console.error('Failed to activate trial:', err);
    alert(err.response?.data?.detail || 'Failed to activate trial. Please try again.');
  }
}
</script>

<style scoped>
.subscription-settings {
  min-height: 100vh;
  background: var(--bg-app, #f9fafb);
  padding: 2rem;
}

.settings-container {
  max-width: 1200px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin-bottom: 0.5rem;
}

.settings-description {
  font-size: 1rem;
  color: var(--text-secondary, #6b7280);
}

/* Loading & Error States */
.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.retry-button {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.retry-button:hover {
  background: #2563eb;
}

/* Messages */
.success-message,
.info-message {
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.success-message {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.info-message {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #3b82f6;
}

.success-icon,
.info-icon {
  font-size: 1.25rem;
}

/* Cards */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.plan-card,
.usage-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-green {
  background: #d1fae5;
  color: #065f46;
}

.status-blue {
  background: #dbeafe;
  color: #1e40af;
}

.status-orange {
  background: #fed7aa;
  color: #92400e;
}

.status-red {
  background: #fee2e2;
  color: #991b1b;
}

.status-gray {
  background: #f3f4f6;
  color: #374151;
}

.plan-info {
  margin-bottom: 2rem;
}

.plan-name-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.plan-icon {
  font-size: 3rem;
}

.plan-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary, #111827);
  margin: 0;
}

.plan-price {
  font-size: 1.125rem;
  color: var(--text-secondary, #6b7280);
  margin: 0.25rem 0 0 0;
}

.trial-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #dbeafe;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.trial-icon {
  font-size: 1.25rem;
}

.trial-text {
  font-weight: 600;
  color: #1e40af;
}

.billing-period {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-top: 1px solid #e5e7eb;
  margin-top: 1rem;
}

.period-label {
  color: var(--text-secondary, #6b7280);
}

.period-date {
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.cancel-info {
  padding: 0.75rem 1rem;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  margin-top: 1rem;
}

.past-due-warning {
  padding: 0.75rem 1rem;
  background: #fef3c7;
  color: #92400e;
  border-radius: 8px;
  margin-top: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.plan-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-button {
  flex: 1;
  min-width: 200px;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.button-primary {
  background: #3b82f6;
  color: white;
}

.button-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.button-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.button-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.button-trial {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
}

.button-trial:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Usage warnings */
.usage-warning {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-top: 1.5rem;
}

.warning-caution {
  background: #fef3c7;
  border: 1px solid #f59e0b;
}

.warning-danger {
  background: #fee2e2;
  border: 1px solid #ef4444;
}

.warning-icon {
  font-size: 1.5rem;
}

.warning-content strong {
  display: block;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.warning-content p {
  margin: 0;
  font-size: 0.875rem;
}

/* Pricing section */
.pricing-section {
  margin-top: 2rem;
}

/* Responsive */
@media (max-width: 768px) {
  .subscription-settings {
    padding: 1rem;
  }

  .settings-title {
    font-size: 1.5rem;
  }

  .plan-actions {
    flex-direction: column;
  }

  .action-button {
    min-width: auto;
  }
}
</style>
