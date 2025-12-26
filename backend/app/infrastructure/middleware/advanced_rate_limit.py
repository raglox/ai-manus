"""
Advanced Rate Limiting with Redis backend
Replaces in-memory rate limiter with distributed, persistent solution
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
import redis.asyncio as redis
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting
    Priority: user_id > API key > IP address
    """
    # Try to get authenticated user_id
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Try to get API key (if implemented)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


def create_rate_limiter(redis_url: str) -> Limiter:
    """
    Create rate limiter with Redis backend
    
    Args:
        redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
    
    Returns:
        Configured Limiter instance
    """
    try:
        limiter = Limiter(
            key_func=get_user_identifier,
            storage_uri=redis_url,
            strategy="fixed-window",  # Can be: fixed-window, moving-window
            default_limits=["100/minute", "1000/hour"],  # Global defaults
            headers_enabled=True,  # Return X-RateLimit-* headers
        )
        logger.info(f"Rate limiter initialized with Redis backend: {redis_url}")
        return limiter
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        # Fallback to in-memory if Redis unavailable
        logger.warning("Falling back to in-memory rate limiter (not recommended for production)")
        return Limiter(
            key_func=get_user_identifier,
            default_limits=["100/minute", "1000/hour"],
        )


# Rate limit configurations by endpoint category
RATE_LIMITS = {
    # Authentication endpoints (strict)
    "auth_login": "5/minute, 20/hour",  # Prevent brute-force
    "auth_register": "3/minute, 10/hour",  # Prevent spam registrations
    "auth_refresh": "10/minute, 50/hour",
    
    # Session/Agent endpoints (moderate)
    "session_create": "10/minute, 100/hour",
    "session_list": "30/minute, 300/hour",
    "agent_execute": "20/minute, 200/hour",
    
    # File endpoints (moderate)
    "file_upload": "10/minute, 50/hour",
    "file_download": "30/minute, 300/hour",
    "file_list": "50/minute, 500/hour",
    
    # Billing endpoints (lenient for legit traffic)
    "billing_subscription": "20/minute, 200/hour",
    "billing_checkout": "5/minute, 20/hour",
    "billing_webhook": "100/minute",  # Stripe webhooks
    
    # Public endpoints (very lenient)
    "health": "300/minute",
    "version": "100/minute",
}


def get_rate_limit(endpoint_category: str) -> str:
    """Get rate limit for specific endpoint category"""
    return RATE_LIMITS.get(endpoint_category, "50/minute, 500/hour")
