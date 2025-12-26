"""Subscription domain model"""

from typing import Optional
from datetime import datetime, UTC
from pydantic import BaseModel, field_validator
from enum import Enum


class SubscriptionPlan(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Subscription(BaseModel):
    """Subscription domain model"""
    id: str
    user_id: str
    plan: SubscriptionPlan = SubscriptionPlan.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Stripe integration
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    
    # Billing details
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    
    # Usage limits
    monthly_agent_runs: int = 0  # Current month's usage
    monthly_agent_runs_limit: int = 10  # Free tier: 10 runs/month
    
    # Trial
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    is_trial: bool = False
    
    # Timestamps
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("User ID is required")
        return v.strip()
    
    def can_use_agent(self) -> bool:
        """Check if user can use the agent based on subscription"""
        # Check if subscription is active
        if self.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
            return False
        
        # Check usage limits
        if self.monthly_agent_runs >= self.monthly_agent_runs_limit:
            return False
        
        # Check if trial has expired
        if self.is_trial and self.trial_end and datetime.now(UTC) > self.trial_end:
            return False
        
        return True
    
    def increment_usage(self):
        """Increment monthly agent runs"""
        self.monthly_agent_runs += 1
        self.updated_at = datetime.now(UTC)
    
    def reset_monthly_usage(self):
        """Reset monthly usage counter (called on billing cycle)"""
        self.monthly_agent_runs = 0
        self.updated_at = datetime.now(UTC)
    
    def upgrade_to_basic(self):
        """Upgrade to Basic plan"""
        self.plan = SubscriptionPlan.BASIC
        self.monthly_agent_runs_limit = 100  # 100 runs/month
        self.updated_at = datetime.now(UTC)
    
    def upgrade_to_pro(self):
        """Upgrade to Pro plan"""
        self.plan = SubscriptionPlan.PRO
        self.monthly_agent_runs_limit = 1000  # 1000 runs/month
        self.updated_at = datetime.now(UTC)
    
    def downgrade_to_free(self):
        """Downgrade to Free plan"""
        self.plan = SubscriptionPlan.FREE
        self.monthly_agent_runs_limit = 10
        self.status = SubscriptionStatus.ACTIVE
        self.stripe_subscription_id = None
        self.stripe_price_id = None
        self.cancel_at_period_end = False
        self.updated_at = datetime.now(UTC)
    
    def cancel(self, immediate: bool = False):
        """Cancel subscription"""
        if immediate:
            self.status = SubscriptionStatus.CANCELED
            self.canceled_at = datetime.now(UTC)
            self.downgrade_to_free()
        else:
            self.cancel_at_period_end = True
            self.updated_at = datetime.now(UTC)
    
    def activate_trial(self, days: int = 14):
        """Activate trial period"""
        from datetime import timedelta
        now = datetime.now(UTC)
        self.is_trial = True
        self.trial_start = now
        self.trial_end = now + timedelta(days=days)
        self.status = SubscriptionStatus.TRIALING
        self.monthly_agent_runs_limit = 50  # Trial: 50 runs
        self.updated_at = now
