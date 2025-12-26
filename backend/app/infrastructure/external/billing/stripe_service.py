"""Stripe billing service for payment processing"""

import stripe
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.domain.repositories.subscription_repository import SubscriptionRepository

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment processing service"""
    
    def __init__(self, subscription_repository: SubscriptionRepository):
        """Initialize Stripe service
        
        Args:
            subscription_repository: Repository for subscription data
        """
        self.subscription_repository = subscription_repository
        
        # Initialize Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            logger.warning("STRIPE_SECRET_KEY not set - Stripe integration disabled")
        
        # Stripe price IDs (set these in environment variables)
        self.price_id_basic = os.getenv("STRIPE_PRICE_ID_BASIC")
        self.price_id_pro = os.getenv("STRIPE_PRICE_ID_PRO")
        
        # Webhook secret
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        logger.info("StripeService initialized")
    
    async def create_customer(self, user_id: str, email: str, name: str) -> str:
        """Create a Stripe customer
        
        Args:
            user_id: User ID
            email: Customer email
            name: Customer name
            
        Returns:
            Stripe customer ID
        """
        try:
            logger.info(f"Creating Stripe customer for user: {user_id}")
            
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": user_id
                }
            )
            
            logger.info(f"Stripe customer created: {customer.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise Exception(f"Failed to create Stripe customer: {str(e)}")
    
    async def create_checkout_session(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session for subscription
        
        Args:
            user_id: User ID
            plan: Subscription plan (BASIC or PRO)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is canceled
            
        Returns:
            Dict with checkout session details
        """
        try:
            logger.info(f"Creating Stripe checkout session for user {user_id}, plan: {plan}")
            
            # Get or create Stripe customer
            subscription = await self.subscription_repository.get_subscription_by_user_id(user_id)
            if not subscription:
                raise ValueError(f"Subscription not found for user: {user_id}")
            
            # Determine price ID based on plan
            if plan == SubscriptionPlan.BASIC:
                price_id = self.price_id_basic
            elif plan == SubscriptionPlan.PRO:
                price_id = self.price_id_pro
            else:
                raise ValueError(f"Invalid plan for checkout: {plan}")
            
            if not price_id:
                raise ValueError(f"Stripe price ID not configured for plan: {plan}")
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan": plan.value
                }
            )
            
            logger.info(f"Checkout session created: {session.id}")
            
            return {
                "checkout_session_id": session.id,
                "checkout_url": session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    async def create_customer_portal_session(
        self,
        user_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session
        
        Args:
            user_id: User ID
            return_url: URL to return to after portal
            
        Returns:
            Dict with portal session URL
        """
        try:
            logger.info(f"Creating customer portal session for user: {user_id}")
            
            subscription = await self.subscription_repository.get_subscription_by_user_id(user_id)
            if not subscription or not subscription.stripe_customer_id:
                raise ValueError(f"No Stripe customer found for user: {user_id}")
            
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url,
            )
            
            logger.info(f"Customer portal session created: {session.id}")
            
            return {
                "portal_url": session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {str(e)}")
            raise Exception(f"Failed to create portal session: {str(e)}")
    
    async def handle_webhook_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            Dict with processing result
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info(f"Processing Stripe webhook event: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return await self._handle_checkout_completed(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.created':
                return await self._handle_subscription_created(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return await self._handle_payment_failed(event['data']['object'])
            
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {"status": "ignored", "event_type": event['type']}
                
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise Exception("Invalid webhook signature")
        
        except Exception as e:
            logger.error(f"Failed to process webhook event: {str(e)}")
            raise
    
    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout.session.completed event"""
        logger.info(f"Handling checkout completed: {session['id']}")
        
        user_id = session['metadata'].get('user_id')
        if not user_id:
            logger.error("No user_id in checkout session metadata")
            return {"status": "error", "message": "Missing user_id"}
        
        # Get subscription
        subscription = await self.subscription_repository.get_subscription_by_user_id(user_id)
        if not subscription:
            logger.error(f"Subscription not found for user: {user_id}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Update subscription with Stripe IDs
        subscription.stripe_customer_id = session['customer']
        subscription.stripe_subscription_id = session['subscription']
        
        # Update and save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.info(f"Checkout completed for user: {user_id}")
        return {"status": "success", "user_id": user_id}
    
    async def _handle_subscription_created(self, stripe_subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.created event"""
        logger.info(f"Handling subscription created: {stripe_subscription['id']}")
        
        # Get subscription by Stripe subscription ID
        subscription = await self.subscription_repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription['id']
        )
        
        if not subscription:
            # Try to find by customer ID
            subscription = await self.subscription_repository.get_subscription_by_stripe_customer_id(
                stripe_subscription['customer']
            )
        
        if not subscription:
            logger.error(f"Subscription not found for Stripe subscription: {stripe_subscription['id']}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Update subscription details
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.stripe_price_id = stripe_subscription['items']['data'][0]['price']['id']
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'], timezone.utc)
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'], timezone.utc)
        
        # Determine plan based on price ID
        if subscription.stripe_price_id == self.price_id_basic:
            subscription.upgrade_to_basic()
        elif subscription.stripe_price_id == self.price_id_pro:
            subscription.upgrade_to_pro()
        
        # Save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.info(f"Subscription activated for user: {subscription.user_id}")
        return {"status": "success", "user_id": subscription.user_id}
    
    async def _handle_subscription_updated(self, stripe_subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.updated event"""
        logger.info(f"Handling subscription updated: {stripe_subscription['id']}")
        
        subscription = await self.subscription_repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription['id']
        )
        
        if not subscription:
            logger.error(f"Subscription not found: {stripe_subscription['id']}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Update subscription details
        subscription.status = SubscriptionStatus(stripe_subscription['status'])
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'], timezone.utc)
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'], timezone.utc)
        subscription.cancel_at_period_end = stripe_subscription['cancel_at_period_end']
        
        # Save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.info(f"Subscription updated for user: {subscription.user_id}")
        return {"status": "success", "user_id": subscription.user_id}
    
    async def _handle_subscription_deleted(self, stripe_subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event"""
        logger.info(f"Handling subscription deleted: {stripe_subscription['id']}")
        
        subscription = await self.subscription_repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription['id']
        )
        
        if not subscription:
            logger.error(f"Subscription not found: {stripe_subscription['id']}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Downgrade to free plan
        subscription.cancel(immediate=True)
        
        # Save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.info(f"Subscription canceled for user: {subscription.user_id}")
        return {"status": "success", "user_id": subscription.user_id}
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event"""
        logger.info(f"Handling payment succeeded: {invoice['id']}")
        
        stripe_subscription_id = invoice.get('subscription')
        if not stripe_subscription_id:
            return {"status": "ignored", "message": "No subscription in invoice"}
        
        subscription = await self.subscription_repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription_id
        )
        
        if not subscription:
            logger.error(f"Subscription not found: {stripe_subscription_id}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Reset monthly usage on successful payment (new billing cycle)
        subscription.reset_monthly_usage()
        subscription.status = SubscriptionStatus.ACTIVE
        
        # Save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.info(f"Payment succeeded for user: {subscription.user_id}")
        return {"status": "success", "user_id": subscription.user_id}
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        logger.info(f"Handling payment failed: {invoice['id']}")
        
        stripe_subscription_id = invoice.get('subscription')
        if not stripe_subscription_id:
            return {"status": "ignored", "message": "No subscription in invoice"}
        
        subscription = await self.subscription_repository.get_subscription_by_stripe_subscription_id(
            stripe_subscription_id
        )
        
        if not subscription:
            logger.error(f"Subscription not found: {stripe_subscription_id}")
            return {"status": "error", "message": "Subscription not found"}
        
        # Mark subscription as past due
        subscription.status = SubscriptionStatus.PAST_DUE
        
        # Save
        await self.subscription_repository.update_subscription(subscription)
        
        logger.warning(f"Payment failed for user: {subscription.user_id}")
        return {"status": "success", "user_id": subscription.user_id}
