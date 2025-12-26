"""Billing API routes for Stripe integration"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from typing import Optional
import logging
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.domain.repositories.subscription_repository import SubscriptionRepository
from app.infrastructure.repositories.subscription_repository import MongoSubscriptionRepository
from app.infrastructure.external.billing.stripe_service import StripeService
from app.interfaces.api.auth_routes import get_current_user
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# Get limiter from app state
limiter = Limiter(key_func=get_remote_address)


# Dependency injection
def get_subscription_repository() -> SubscriptionRepository:
    """Get subscription repository instance"""
    return MongoSubscriptionRepository()


def get_stripe_service(
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository)
) -> StripeService:
    """Get Stripe service instance"""
    return StripeService(subscription_repository)


# Request/Response models
class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    plan: SubscriptionPlan
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreateCheckoutSessionResponse(BaseModel):
    """Response with Stripe checkout session details"""
    checkout_session_id: str
    checkout_url: str


class SubscriptionResponse(BaseModel):
    """Subscription status response"""
    id: str
    user_id: str
    plan: str
    status: str
    monthly_agent_runs: int
    monthly_agent_runs_limit: int
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    is_trial: bool = False
    trial_end: Optional[str] = None


class CustomerPortalResponse(BaseModel):
    """Customer portal URL response"""
    portal_url: str


# Routes
@router.post("/create-checkout-session", response_model=CreateCheckoutSessionResponse)
@limiter.limit("5/minute;20/hour")  # Limit checkout session creation
async def create_checkout_session(
    http_request: Request,
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository)
):
    """Create a Stripe checkout session for subscription upgrade (Rate limited: 5 req/min, 20 req/hour)
    
    This endpoint creates a Stripe Checkout session that redirects the user
    to Stripe's hosted payment page.
    """
    try:
        # Validate plan
        if request.plan not in [SubscriptionPlan.BASIC, SubscriptionPlan.PRO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan: {request.plan}. Only BASIC and PRO are available."
            )
        
        # Get or create subscription
        subscription = await subscription_repository.get_subscription_by_user_id(current_user.id)
        if not subscription:
            # Create free subscription if doesn't exist
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE
            )
            
            # Create Stripe customer
            stripe_customer_id = await stripe_service.create_customer(
                user_id=current_user.id,
                email=current_user.email,
                name=current_user.fullname
            )
            subscription.stripe_customer_id = stripe_customer_id
            
            await subscription_repository.create_subscription(subscription)
        
        # Set default URLs if not provided
        success_url = request.success_url or "http://localhost:3000/settings/subscription?success=true"
        cancel_url = request.cancel_url or "http://localhost:3000/settings/subscription?canceled=true"
        
        # Create checkout session
        result = await stripe_service.create_checkout_session(
            user_id=current_user.id,
            plan=request.plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return CreateCheckoutSessionResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/create-portal-session", response_model=CustomerPortalResponse)
@limiter.limit("10/minute;50/hour")  # Moderate limit for portal sessions
async def create_customer_portal_session(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
    return_url: Optional[str] = None
):
    """Create a Stripe Customer Portal session (Rate limited: 10 req/min, 50 req/hour)
    
    This endpoint creates a session for the Stripe Customer Portal where users
    can manage their subscription, update payment methods, and view invoices.
    """
    try:
        # Set default return URL
        return_url = return_url or "http://localhost:3000/settings/subscription"
        
        # Create portal session
        result = await stripe_service.create_customer_portal_session(
            user_id=current_user.id,
            return_url=return_url
        )
        
        return CustomerPortalResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create portal session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
@limiter.limit("30/minute;300/hour")  # Generous limit for read operations
async def get_subscription(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository)
):
    """Get current user's subscription status (Rate limited: 30 req/min, 300 req/hour)"""
    try:
        subscription = await subscription_repository.get_subscription_by_user_id(current_user.id)
        
        if not subscription:
            # Create free subscription if doesn't exist
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE
            )
            await subscription_repository.create_subscription(subscription)
        
        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan.value,
            status=subscription.status.value,
            monthly_agent_runs=subscription.monthly_agent_runs,
            monthly_agent_runs_limit=subscription.monthly_agent_runs_limit,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            is_trial=subscription.is_trial,
            trial_end=subscription.trial_end.isoformat() if subscription.trial_end else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.post("/webhook")
@limiter.limit("100/minute")  # Strict limit for webhook to prevent abuse
async def stripe_webhook(
    http_request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Handle Stripe webhook events with rate limiting (100 req/min)
    
    This endpoint receives webhook events from Stripe to keep subscription
    status in sync with Stripe's records.
    """
    try:
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe-Signature header"
            )
        
        # Get raw body
        body = await http_request.body()
        
        # Process webhook event
        result = await stripe_service.handle_webhook_event(body, stripe_signature)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/activate-trial")
@limiter.limit("3/hour")  # Very strict - trial activation once per user
async def activate_trial(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Activate trial period for new users (Rate limited: 3 req/hour)"""
    try:
        subscription = await subscription_repository.get_subscription_by_user_id(current_user.id)
        
        if not subscription:
            # Create subscription with trial
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.TRIALING
            )
            
            # Create Stripe customer
            stripe_customer_id = await stripe_service.create_customer(
                user_id=current_user.id,
                email=current_user.email,
                name=current_user.fullname
            )
            subscription.stripe_customer_id = stripe_customer_id
            
            # Activate trial (14 days, 50 runs)
            subscription.activate_trial(days=14)
            
            await subscription_repository.create_subscription(subscription)
            
            return {
                "message": "Trial activated successfully",
                "trial_end": subscription.trial_end.isoformat(),
                "runs_limit": subscription.monthly_agent_runs_limit
            }
        
        elif subscription.is_trial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trial already activated"
            )
        
        elif subscription.plan != SubscriptionPlan.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot activate trial for paid subscription"
            )
        
        # Activate trial for existing free subscription
        subscription.activate_trial(days=14)
        await subscription_repository.update_subscription(subscription)
        
        return {
            "message": "Trial activated successfully",
            "trial_end": subscription.trial_end.isoformat(),
            "runs_limit": subscription.monthly_agent_runs_limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate trial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate trial"
        )
