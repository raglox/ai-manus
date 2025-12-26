/**
 * Composable for managing subscription state and operations
 */

import { ref, computed, onMounted } from 'vue';
import type { Ref } from 'vue';
import {
  getSubscription,
  createCheckoutSession,
  createCustomerPortalSession,
  activateTrial,
  type Subscription,
  type CreateCheckoutSessionRequest,
  SubscriptionPlan,
  SubscriptionStatus,
  canRunAgent,
  getRemainingRuns,
  getUsagePercentage,
  isApproachingLimit,
  isLimitReached,
  getPlanDisplayName,
  getPlanPrice,
  getPlanRunsLimit,
  formatRunsLimit,
  getStatusColor,
  getStatusDisplayText,
  isSubscriptionActive,
  getTrialDaysRemaining,
  formatDate
} from '@/api/billing';

export interface UseSubscriptionReturn {
  // State
  subscription: Ref<Subscription | null>;
  loading: Ref<boolean>;
  error: Ref<Error | null>;
  
  // Computed
  canRun: Ref<boolean>;
  remainingRuns: Ref<number>;
  usagePercentage: Ref<number>;
  isApproaching: Ref<boolean>;
  isLimitExceeded: Ref<boolean>;
  planName: Ref<string>;
  planPrice: Ref<number | null>;
  statusColor: Ref<string>;
  statusText: Ref<string>;
  isActive: Ref<boolean>;
  trialDaysLeft: Ref<number | null>;
  formattedPeriodEnd: Ref<string | null>;
  
  // Methods
  fetchSubscription: () => Promise<void>;
  upgradeSubscription: (plan: SubscriptionPlan.BASIC | SubscriptionPlan.PRO) => Promise<void>;
  openCustomerPortal: () => Promise<void>;
  startTrial: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Use subscription hook
 */
export function useSubscription(): UseSubscriptionReturn {
  // State
  const subscription = ref<Subscription | null>(null);
  const loading = ref(false);
  const error = ref<Error | null>(null);

  // Computed properties
  const canRun = computed(() => 
    subscription.value ? canRunAgent(subscription.value) : false
  );

  const remainingRuns = computed(() => 
    subscription.value ? getRemainingRuns(subscription.value) : 0
  );

  const usagePercentage = computed(() => 
    subscription.value ? getUsagePercentage(subscription.value) : 0
  );

  const isApproaching = computed(() => 
    subscription.value ? isApproachingLimit(subscription.value) : false
  );

  const isLimitExceeded = computed(() => 
    subscription.value ? isLimitReached(subscription.value) : false
  );

  const planName = computed(() => 
    subscription.value ? getPlanDisplayName(subscription.value.plan) : 'Unknown'
  );

  const planPrice = computed(() => 
    subscription.value ? getPlanPrice(subscription.value.plan) : null
  );

  const statusColor = computed(() => 
    subscription.value ? getStatusColor(subscription.value.status) : 'gray'
  );

  const statusText = computed(() => 
    subscription.value ? getStatusDisplayText(subscription.value.status) : 'Unknown'
  );

  const isActive = computed(() => 
    subscription.value ? isSubscriptionActive(subscription.value) : false
  );

  const trialDaysLeft = computed(() => 
    subscription.value ? getTrialDaysRemaining(subscription.value) : null
  );

  const formattedPeriodEnd = computed(() => 
    subscription.value ? formatDate(subscription.value.current_period_end) : null
  );

  // Methods
  /**
   * Fetch subscription from API
   */
  async function fetchSubscription(): Promise<void> {
    loading.value = true;
    error.value = null;
    
    try {
      subscription.value = await getSubscription();
    } catch (err) {
      error.value = err as Error;
      console.error('Failed to fetch subscription:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Upgrade subscription to a paid plan
   */
  async function upgradeSubscription(
    plan: SubscriptionPlan.BASIC | SubscriptionPlan.PRO
  ): Promise<void> {
    loading.value = true;
    error.value = null;
    
    try {
      const request: CreateCheckoutSessionRequest = {
        plan,
        success_url: `${window.location.origin}/settings/subscription?success=true`,
        cancel_url: `${window.location.origin}/settings/subscription?canceled=true`
      };
      
      const response = await createCheckoutSession(request);
      
      // Redirect to Stripe Checkout
      window.location.href = response.checkout_url;
    } catch (err) {
      error.value = err as Error;
      console.error('Failed to create checkout session:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Open Stripe Customer Portal
   */
  async function openCustomerPortal(): Promise<void> {
    loading.value = true;
    error.value = null;
    
    try {
      const returnUrl = `${window.location.origin}/settings/subscription`;
      const response = await createCustomerPortalSession(returnUrl);
      
      // Open portal in new tab
      window.open(response.portal_url, '_blank');
    } catch (err) {
      error.value = err as Error;
      console.error('Failed to create portal session:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Start trial period
   */
  async function startTrial(): Promise<void> {
    loading.value = true;
    error.value = null;
    
    try {
      await activateTrial();
      // Refresh subscription data
      await fetchSubscription();
    } catch (err) {
      error.value = err as Error;
      console.error('Failed to activate trial:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Refresh subscription data
   */
  async function refresh(): Promise<void> {
    await fetchSubscription();
  }

  // Fetch on mount
  onMounted(() => {
    fetchSubscription();
  });

  return {
    // State
    subscription,
    loading,
    error,
    
    // Computed
    canRun,
    remainingRuns,
    usagePercentage,
    isApproaching,
    isLimitExceeded,
    planName,
    planPrice,
    statusColor,
    statusText,
    isActive,
    trialDaysLeft,
    formattedPeriodEnd,
    
    // Methods
    fetchSubscription,
    upgradeSubscription,
    openCustomerPortal,
    startTrial,
    refresh
  };
}

// Export helper functions for use in components
export {
  getPlanDisplayName,
  getPlanPrice,
  getPlanRunsLimit,
  formatRunsLimit,
  getStatusColor,
  getStatusDisplayText,
  formatDate
};
