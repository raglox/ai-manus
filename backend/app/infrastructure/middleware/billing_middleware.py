"""Billing middleware to protect API endpoints based on subscription status"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from app.domain.repositories.subscription_repository import SubscriptionRepository

logger = logging.getLogger(__name__)


class BillingMiddleware(BaseHTTPMiddleware):
    """Middleware to check subscription status before allowing agent usage"""
    
    # Endpoints that require active subscription
    PROTECTED_ENDPOINTS = [
        "/api/v1/sessions",  # Creating sessions
        "/api/v1/agent/execute",  # Running agent
        "/api/v1/sandbox",  # Sandbox operations
    ]
    
    # Endpoints that are always allowed (auth, billing, etc.)
    ALLOWED_ENDPOINTS = [
        "/api/v1/auth",
        "/api/v1/billing",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/api/v1/files",  # Allow file access
    ]
    
    def __init__(self, app, subscription_repository: SubscriptionRepository):
        super().__init__(app)
        self.subscription_repository = subscription_repository
    
    async def dispatch(self, request: Request, call_next):
        """Check subscription before processing request"""
        
        # Skip check for allowed endpoints
        if self._is_allowed_endpoint(request.url.path):
            return await call_next(request)
        
        # Skip check for non-protected endpoints
        if not self._is_protected_endpoint(request.url.path):
            return await call_next(request)
        
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            logger.warning(f"No user_id found for protected endpoint: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        
        # Check subscription status
        try:
            subscription = await self.subscription_repository.get_subscription_by_user_id(user_id)
            
            if not subscription:
                logger.warning(f"No subscription found for user: {user_id}")
                return JSONResponse(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    content={
                        "detail": "No subscription found. Please subscribe to use this feature.",
                        "error_code": "NO_SUBSCRIPTION"
                    }
                )
            
            # Check if user can use agent
            if not subscription.can_use_agent():
                logger.warning(f"Subscription limit reached for user: {user_id}")
                return JSONResponse(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    content={
                        "detail": self._get_limit_message(subscription),
                        "error_code": "SUBSCRIPTION_LIMIT_REACHED",
                        "subscription": {
                            "plan": subscription.plan.value,
                            "status": subscription.status.value,
                            "monthly_runs": subscription.monthly_agent_runs,
                            "monthly_runs_limit": subscription.monthly_agent_runs_limit
                        }
                    }
                )
            
            # Increment usage for session creation
            if request.method == "POST" and "/sessions" in request.url.path:
                subscription.increment_usage()
                await self.subscription_repository.update_subscription(subscription)
                logger.info(f"Usage incremented for user {user_id}: {subscription.monthly_agent_runs}/{subscription.monthly_agent_runs_limit}")
            
            # Store subscription in request state for downstream use
            request.state.subscription = subscription
            
            # Continue with request
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error checking subscription: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Error checking subscription status"}
            )
    
    def _is_protected_endpoint(self, path: str) -> bool:
        """Check if endpoint requires subscription"""
        return any(path.startswith(endpoint) for endpoint in self.PROTECTED_ENDPOINTS)
    
    def _is_allowed_endpoint(self, path: str) -> bool:
        """Check if endpoint is always allowed"""
        return any(path.startswith(endpoint) for endpoint in self.ALLOWED_ENDPOINTS)
    
    def _get_limit_message(self, subscription) -> str:
        """Get appropriate error message based on subscription status"""
        from app.domain.models.subscription import SubscriptionStatus
        
        if subscription.status in [SubscriptionStatus.CANCELED, SubscriptionStatus.UNPAID]:
            return "Your subscription is inactive. Please renew to continue using the agent."
        
        if subscription.monthly_agent_runs >= subscription.monthly_agent_runs_limit:
            return f"You have reached your monthly limit of {subscription.monthly_agent_runs_limit} agent runs. Please upgrade your plan to continue."
        
        if subscription.is_trial and subscription.trial_end:
            from datetime import datetime, UTC
            if datetime.now(UTC) > subscription.trial_end:
                return "Your trial period has expired. Please subscribe to continue using the agent."
        
        return "Your subscription does not allow agent usage. Please check your subscription status."
