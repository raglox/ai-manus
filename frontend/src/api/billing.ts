/**
 * Billing API - Stripe integration for subscription management
 */

import { apiClient } from './client';

// ==================== Types ====================

/**
 * Subscription plans
 */
export enum SubscriptionPlan {
  FREE = 'FREE',
  BASIC = 'BASIC',
  PRO = 'PRO',
  ENTERPRISE = 'ENTERPRISE'
}

/**
 * Subscription status
 */
export enum SubscriptionStatus {
  ACTIVE = 'ACTIVE',
  TRIALING = 'TRIALING',
  PAST_DUE = 'PAST_DUE',
  CANCELED = 'CANCELED',
  INCOMPLETE = 'INCOMPLETE'
}

/**
 * Subscription information
 */
export interface Subscription {
  id: string;
  user_id: string;
  plan: SubscriptionPlan;
  status: SubscriptionStatus;
  monthly_agent_runs: number;
  monthly_agent_runs_limit: number;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_trial: boolean;
  trial_end: string | null;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Request to create checkout session
 */
export interface CreateCheckoutSessionRequest {
  plan: SubscriptionPlan.BASIC | SubscriptionPlan.PRO;
  success_url?: string;
  cancel_url?: string;
}

/**
 * Response from create checkout session
 */
export interface CreateCheckoutSessionResponse {
  checkout_session_id: string;
  checkout_url: string;
}

/**
 * Response from create customer portal session
 */
export interface CustomerPortalResponse {
  portal_url: string;
}

/**
 * Trial activation response
 */
export interface TrialActivationResponse {
  message: string;
  trial_end: string;
  runs_limit: number;
}

// ==================== API Functions ====================

/**
 * Get current user's subscription
 */
export async function getSubscription(): Promise<Subscription> {
  const response = await apiClient.get<Subscription>('/billing/subscription');
  return response.data;
}

/**
 * Create Stripe checkout session for subscription upgrade
 */
export async function createCheckoutSession(
  request: CreateCheckoutSessionRequest
): Promise<CreateCheckoutSessionResponse> {
  const response = await apiClient.post<CreateCheckoutSessionResponse>(
    '/billing/create-checkout-session',
    request
  );
  return response.data;
}

/**
 * Create Stripe customer portal session
 */
export async function createCustomerPortalSession(
  returnUrl?: string
): Promise<CustomerPortalResponse> {
  const response = await apiClient.post<CustomerPortalResponse>(
    '/billing/create-portal-session',
    returnUrl ? { return_url: returnUrl } : undefined
  );
  return response.data;
}

/**
 * Activate trial period (14 days, 50 runs)
 */
export async function activateTrial(): Promise<TrialActivationResponse> {
  const response = await apiClient.post<TrialActivationResponse>(
    '/billing/activate-trial'
  );
  return response.data;
}

// ==================== Helper Functions ====================

/**
 * Check if user can run agent (has remaining runs)
 */
export function canRunAgent(subscription: Subscription): boolean {
  return subscription.monthly_agent_runs < subscription.monthly_agent_runs_limit;
}

/**
 * Get remaining runs
 */
export function getRemainingRuns(subscription: Subscription): number {
  return Math.max(
    0,
    subscription.monthly_agent_runs_limit - subscription.monthly_agent_runs
  );
}

/**
 * Get usage percentage
 */
export function getUsagePercentage(subscription: Subscription): number {
  if (subscription.monthly_agent_runs_limit === 0) return 0;
  return Math.min(
    100,
    (subscription.monthly_agent_runs / subscription.monthly_agent_runs_limit) * 100
  );
}

/**
 * Check if approaching limit (>= 80%)
 */
export function isApproachingLimit(subscription: Subscription): boolean {
  return getUsagePercentage(subscription) >= 80;
}

/**
 * Check if limit reached
 */
export function isLimitReached(subscription: Subscription): boolean {
  return subscription.monthly_agent_runs >= subscription.monthly_agent_runs_limit;
}

/**
 * Get plan display name
 */
export function getPlanDisplayName(plan: SubscriptionPlan): string {
  const names: Record<SubscriptionPlan, string> = {
    [SubscriptionPlan.FREE]: 'Free',
    [SubscriptionPlan.BASIC]: 'Basic',
    [SubscriptionPlan.PRO]: 'Pro',
    [SubscriptionPlan.ENTERPRISE]: 'Enterprise'
  };
  return names[plan];
}

/**
 * Get plan price
 */
export function getPlanPrice(plan: SubscriptionPlan): number | null {
  const prices: Record<SubscriptionPlan, number | null> = {
    [SubscriptionPlan.FREE]: 0,
    [SubscriptionPlan.BASIC]: 19,
    [SubscriptionPlan.PRO]: 49,
    [SubscriptionPlan.ENTERPRISE]: null // Custom pricing
  };
  return prices[plan];
}

/**
 * Get plan runs limit
 */
export function getPlanRunsLimit(plan: SubscriptionPlan): number {
  const limits: Record<SubscriptionPlan, number> = {
    [SubscriptionPlan.FREE]: 10,
    [SubscriptionPlan.BASIC]: 1000,
    [SubscriptionPlan.PRO]: 5000,
    [SubscriptionPlan.ENTERPRISE]: -1 // Unlimited
  };
  return limits[plan];
}

/**
 * Format runs limit for display
 */
export function formatRunsLimit(limit: number): string {
  if (limit < 0) return 'Unlimited';
  if (limit >= 1000) return `${(limit / 1000).toFixed(0)}K`;
  return limit.toString();
}

/**
 * Get status color
 */
export function getStatusColor(status: SubscriptionStatus): string {
  const colors: Record<SubscriptionStatus, string> = {
    [SubscriptionStatus.ACTIVE]: 'green',
    [SubscriptionStatus.TRIALING]: 'blue',
    [SubscriptionStatus.PAST_DUE]: 'orange',
    [SubscriptionStatus.CANCELED]: 'red',
    [SubscriptionStatus.INCOMPLETE]: 'gray'
  };
  return colors[status];
}

/**
 * Get status display text
 */
export function getStatusDisplayText(status: SubscriptionStatus): string {
  const texts: Record<SubscriptionStatus, string> = {
    [SubscriptionStatus.ACTIVE]: 'Active',
    [SubscriptionStatus.TRIALING]: 'Trial',
    [SubscriptionStatus.PAST_DUE]: 'Past Due',
    [SubscriptionStatus.CANCELED]: 'Canceled',
    [SubscriptionStatus.INCOMPLETE]: 'Incomplete'
  };
  return texts[status];
}

/**
 * Check if subscription is active (can use service)
 */
export function isSubscriptionActive(subscription: Subscription): boolean {
  return (
    subscription.status === SubscriptionStatus.ACTIVE ||
    subscription.status === SubscriptionStatus.TRIALING
  );
}

/**
 * Get days remaining in trial
 */
export function getTrialDaysRemaining(subscription: Subscription): number | null {
  if (!subscription.is_trial || !subscription.trial_end) return null;
  
  const trialEnd = new Date(subscription.trial_end);
  const now = new Date();
  const diffTime = trialEnd.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return Math.max(0, diffDays);
}

/**
 * Format date for display
 */
export function formatDate(dateString: string | null): string | null {
  if (!dateString) return null;
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}
