"""MongoDB implementation of SubscriptionRepository"""

from typing import Optional
from app.domain.models.subscription import Subscription
from app.domain.repositories.subscription_repository import SubscriptionRepository
from app.infrastructure.models.documents import SubscriptionDocument
import logging

logger = logging.getLogger(__name__)


class MongoSubscriptionRepository(SubscriptionRepository):
    """MongoDB implementation of SubscriptionRepository"""
    
    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Create a new subscription"""
        logger.info(f"Creating subscription for user: {subscription.user_id}")
        
        # Convert domain model to document
        subscription_doc = SubscriptionDocument.from_domain(subscription)
        
        # Save to database
        await subscription_doc.create()
        
        # Convert back to domain model
        result = subscription_doc.to_domain()
        logger.info(f"Subscription created successfully: {result.id}")
        return result
    
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        logger.debug(f"Getting subscription by ID: {subscription_id}")
        
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.subscription_id == subscription_id
        )
        if not subscription_doc:
            logger.debug(f"Subscription not found: {subscription_id}")
            return None
        
        return subscription_doc.to_domain()
    
    async def get_subscription_by_user_id(self, user_id: str) -> Optional[Subscription]:
        """Get subscription by user ID"""
        logger.debug(f"Getting subscription by user ID: {user_id}")
        
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.user_id == user_id
        )
        if not subscription_doc:
            logger.debug(f"Subscription not found for user: {user_id}")
            return None
        
        return subscription_doc.to_domain()
    
    async def get_subscription_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID"""
        logger.debug(f"Getting subscription by Stripe customer ID: {stripe_customer_id}")
        
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.stripe_customer_id == stripe_customer_id
        )
        if not subscription_doc:
            logger.debug(f"Subscription not found for Stripe customer: {stripe_customer_id}")
            return None
        
        return subscription_doc.to_domain()
    
    async def get_subscription_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        logger.debug(f"Getting subscription by Stripe subscription ID: {stripe_subscription_id}")
        
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.stripe_subscription_id == stripe_subscription_id
        )
        if not subscription_doc:
            logger.debug(f"Subscription not found for Stripe subscription: {stripe_subscription_id}")
            return None
        
        return subscription_doc.to_domain()
    
    async def update_subscription(self, subscription: Subscription) -> Subscription:
        """Update subscription"""
        logger.info(f"Updating subscription: {subscription.id}")
        
        # Find existing document
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.subscription_id == subscription.id
        )
        if not subscription_doc:
            raise ValueError(f"Subscription not found: {subscription.id}")
        
        # Update document from domain model
        subscription_doc.update_from_domain(subscription)
        
        # Save to database
        await subscription_doc.save()
        
        # Convert back to domain model
        result = subscription_doc.to_domain()
        logger.info(f"Subscription updated successfully: {result.id}")
        return result
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete subscription"""
        logger.info(f"Deleting subscription: {subscription_id}")
        
        subscription_doc = await SubscriptionDocument.find_one(
            SubscriptionDocument.subscription_id == subscription_id
        )
        if not subscription_doc:
            logger.warning(f"Subscription not found for deletion: {subscription_id}")
            return False
        
        await subscription_doc.delete()
        logger.info(f"Subscription deleted successfully: {subscription_id}")
        return True
