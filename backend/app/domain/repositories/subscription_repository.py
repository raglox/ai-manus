"""Subscription repository interface"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.subscription import Subscription


class SubscriptionRepository(ABC):
    """Subscription repository interface"""
    
    @abstractmethod
    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Create a new subscription"""
        pass
    
    @abstractmethod
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        pass
    
    @abstractmethod
    async def get_subscription_by_user_id(self, user_id: str) -> Optional[Subscription]:
        """Get subscription by user ID"""
        pass
    
    @abstractmethod
    async def get_subscription_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID"""
        pass
    
    @abstractmethod
    async def get_subscription_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription: Subscription) -> Subscription:
        """Update subscription"""
        pass
    
    @abstractmethod
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete subscription"""
        pass
