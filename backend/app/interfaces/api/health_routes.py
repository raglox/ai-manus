"""Health check endpoints for monitoring and orchestration"""

from fastapi import APIRouter, status, Response
from datetime import datetime, timezone
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint
    
    Returns 200 if application is running
    Used by: Load balancers, uptime monitors
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "manus-ai-backend"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    
    Returns:
        200: All dependencies ready, can accept traffic
        503: One or more dependencies not ready
    
    Used by: Kubernetes readiness probes, load balancers
    """
    checks = {
        "mongodb": {"status": "unknown", "message": ""},
        "redis": {"status": "unknown", "message": ""},
        "stripe": {"status": "unknown", "message": ""}
    }
    
    # Check MongoDB
    try:
        from app.infrastructure.storage.mongodb import get_mongodb
        await get_mongodb().client.admin.command('ping')
        checks["mongodb"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["mongodb"] = {"status": "unhealthy", "message": str(e)}
        logger.error(f"MongoDB health check failed: {e}")
    
    # Check Redis
    try:
        from app.infrastructure.storage.redis import get_redis
        await get_redis().client.ping()
        checks["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "message": str(e)}
        logger.error(f"Redis health check failed: {e}")
    
    # Check Stripe (if configured)
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key and stripe_key.startswith("sk_"):
        try:
            import stripe
            stripe.api_key = stripe_key
            stripe.Account.retrieve()
            checks["stripe"] = {"status": "healthy", "message": "API accessible"}
        except Exception as e:
            checks["stripe"] = {"status": "unhealthy", "message": str(e)}
            logger.error(f"Stripe health check failed: {e}")
    else:
        checks["stripe"] = {"status": "skipped", "message": "Not configured"}
    
    # Determine overall status
    all_critical_healthy = (
        checks["mongodb"]["status"] == "healthy" and
        checks["redis"]["status"] == "healthy"
    )
    
    status_code = status.HTTP_200_OK if all_critical_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        content={
            "status": "ready" if all_critical_healthy else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }.__str__(),
        status_code=status_code,
        media_type="application/json"
    )


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness check - verifies application is alive and not deadlocked
    
    Returns 200 if application process is responsive
    Used by: Kubernetes liveness probes
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "unknown"  # TODO: Track application start time
    }


@router.get("/version", status_code=status.HTTP_200_OK)
async def version_info():
    """
    Version information endpoint
    
    Returns application version, commit hash, build time
    Useful for: Deployment verification, debugging
    """
    return {
        "version": os.getenv("APP_VERSION", "development"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@router.get("/sentry-test", status_code=status.HTTP_200_OK)
async def sentry_test():
    """
    Test Sentry error tracking
    
    DEVELOPMENT ONLY - Remove in production!
    Triggers a test error to verify Sentry is capturing exceptions
    """
    import sentry_sdk
    
    # Check if Sentry is configured
    if not sentry_sdk.Hub.current.client:
        return {
            "status": "error",
            "message": "Sentry not configured. Set SENTRY_DSN in environment."
        }
    
    # Log info (captured as breadcrumb)
    logger.info("Sentry test initiated")
    
    # Capture a test message
    sentry_sdk.capture_message("Sentry test message from health endpoint", level="info")
    
    # Capture a test exception
    try:
        # This will be caught and sent to Sentry
        1 / 0
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Test exception captured by Sentry: {e}")
    
    return {
        "status": "success",
        "message": "Test error and message sent to Sentry. Check your Sentry dashboard.",
        "sentry_configured": True
    }


@router.get("/sentry-debug", status_code=status.HTTP_200_OK)
async def sentry_debug():
    """
    Debug endpoint to check Sentry configuration
    
    Returns Sentry initialization status without triggering errors
    """
    import sentry_sdk
    
    hub = sentry_sdk.Hub.current
    client = hub.client
    
    if not client:
        return {
            "sentry_configured": False,
            "message": "Sentry DSN not set. Set SENTRY_DSN in environment variables."
        }
    
    return {
        "sentry_configured": True,
        "environment": os.getenv("SENTRY_ENVIRONMENT", "production"),
        "dsn_set": bool(os.getenv("SENTRY_DSN")),
        "message": "Sentry is configured and ready to capture errors"
    }
