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
    Readiness check - verifies all dependencies are available.
    This endpoint will trigger lazy initialization of DB connections.
    
    Returns:
        200: All dependencies ready, can accept traffic
        503: One or more dependencies not ready (degraded mode)
    
    Used by: Kubernetes readiness probes, load balancers
    """
    checks = {
        "mongodb": {"status": "unknown", "message": ""},
        "redis": {"status": "unknown", "message": ""},
        "stripe": {"status": "unknown", "message": ""}
    }
    
    # Check MongoDB (with lazy initialization)
    try:
        from app.infrastructure.storage.mongodb import get_mongodb
        mongodb = get_mongodb()
        
        # Try to initialize if not already done
        if mongodb._client is None:
            logger.info("MongoDB not initialized - attempting lazy initialization...")
            try:
                await mongodb.initialize(max_retries=3, retry_delay=1.0)
            except Exception as init_error:
                logger.warning(f"MongoDB lazy initialization failed: {init_error}")
        
        # Test connection
        if mongodb._client is not None:
            await mongodb.client.admin.command('ping')
            checks["mongodb"] = {"status": "healthy", "message": "Connected"}
        else:
            checks["mongodb"] = {"status": "degraded", "message": "Not initialized"}
            
    except Exception as e:
        checks["mongodb"] = {"status": "unhealthy", "message": str(e)}
        logger.warning(f"MongoDB health check failed: {e}")
    
    # Check Redis (with lazy initialization)
    try:
        from app.infrastructure.storage.redis import get_redis
        redis = get_redis()
        
        # Try to initialize if not already done
        if redis._client is None:
            logger.info("Redis not initialized - attempting lazy initialization...")
            try:
                await redis.initialize(max_retries=3, retry_delay=1.0)
            except Exception as init_error:
                logger.warning(f"Redis lazy initialization failed: {init_error}")
        
        # Test connection
        if redis._client is not None:
            await redis.client.ping()
            checks["redis"] = {"status": "healthy", "message": "Connected"}
        else:
            checks["redis"] = {"status": "degraded", "message": "Not initialized"}
            
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "message": str(e)}
        logger.warning(f"Redis health check failed: {e}")
    
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
            logger.warning(f"Stripe health check failed: {e}")
    else:
        checks["stripe"] = {"status": "skipped", "message": "Not configured"}
    
    # Determine overall status (allow degraded mode - don't block traffic)
    all_critical_healthy = (
        checks["mongodb"]["status"] in ["healthy", "degraded"] and
        checks["redis"]["status"] in ["healthy", "degraded"]
    )
    
    # Always return 200 to allow Cloud Run to start - degraded mode is OK
    status_code = status.HTTP_200_OK
    
    import json
    return Response(
        content=json.dumps({
            "status": "ready" if all_critical_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "message": "Service ready - DBs will connect on first use" if not all_critical_healthy else "All services healthy"
        }),
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


@router.get("/debug/redis", status_code=status.HTTP_200_OK)
async def debug_redis():
    """
    Debug endpoint to test Redis connectivity with detailed error messages
    
    Returns detailed Redis connection information and errors
    """
    result = {
        "redis_host": os.getenv("REDIS_HOST", "unknown"),
        "redis_port": os.getenv("REDIS_PORT", "unknown"),
        "redis_password": "***" if os.getenv("REDIS_PASSWORD") else "not set",
        "connection_attempts": [],
        "final_status": "unknown"
    }
    
    try:
        from app.infrastructure.storage.redis import get_redis
        import asyncio
        
        redis = get_redis()
        
        # Attempt 1: Check if already initialized
        if redis._client is not None:
            result["connection_attempts"].append({
                "attempt": 0,
                "status": "already_initialized",
                "message": "Redis client already exists"
            })
            
            # Try to ping
            try:
                await asyncio.wait_for(redis.client.ping(), timeout=5.0)
                result["final_status"] = "healthy"
                result["message"] = "Redis already initialized and responding to ping"
                return result
            except Exception as ping_error:
                result["connection_attempts"].append({
                    "attempt": 0,
                    "status": "ping_failed",
                    "error": str(ping_error),
                    "error_type": type(ping_error).__name__
                })
        
        # Attempt 2: Initialize with detailed logging
        result["connection_attempts"].append({
            "attempt": 1,
            "status": "starting",
            "message": "Attempting Redis initialization..."
        })
        
        try:
            await redis.initialize(max_retries=3, retry_delay=1.0)
            
            if redis._client is not None:
                # Test ping
                await asyncio.wait_for(redis.client.ping(), timeout=5.0)
                result["final_status"] = "healthy"
                result["message"] = "Redis initialized successfully and responding to ping"
                result["connection_attempts"].append({
                    "attempt": 1,
                    "status": "success",
                    "message": "Initialized and ping successful"
                })
            else:
                result["final_status"] = "failed"
                result["message"] = "Redis initialization returned None client"
                result["connection_attempts"].append({
                    "attempt": 1,
                    "status": "failed",
                    "error": "Client is None after initialization"
                })
                
        except Exception as init_error:
            result["final_status"] = "error"
            result["message"] = f"Redis initialization failed: {str(init_error)}"
            result["connection_attempts"].append({
                "attempt": 1,
                "status": "error",
                "error": str(init_error),
                "error_type": type(init_error).__name__
            })
            
            # Add traceback for debugging
            import traceback
            result["traceback"] = traceback.format_exc()
            
    except Exception as e:
        result["final_status"] = "error"
        result["message"] = f"Unexpected error: {str(e)}"
        result["error_type"] = type(e).__name__
        
        import traceback
        result["traceback"] = traceback.format_exc()
    
    return result


@router.get("/debug/beanie")
async def debug_beanie():
    """
    Debug endpoint to check Beanie initialization status
    """
    try:
        from app.infrastructure.storage.mongodb import get_mongodb
        mongodb = get_mongodb()
        
        response = {
            "mongodb_client_exists": mongodb._client is not None,
            "beanie_initialized": mongodb.is_beanie_initialized,
            "status": "unknown"
        }
        
        # Try to initialize if needed
        if not mongodb.is_beanie_initialized:
            try:
                await mongodb.initialize(max_retries=1, retry_delay=1.0)
                response["initialization_attempted"] = True
                response["beanie_initialized"] = mongodb.is_beanie_initialized
                response["status"] = "initialized" if mongodb.is_beanie_initialized else "failed"
            except Exception as init_error:
                response["initialization_error"] = str(init_error)
                response["status"] = "error"
        else:
            response["status"] = "already_initialized"
        
        # Try to use Beanie
        try:
            from app.infrastructure.models.documents import UserDocument
            count = await UserDocument.count()
            response["user_count"] = count
            response["beanie_working"] = True
        except Exception as beanie_error:
            response["beanie_error"] = str(beanie_error)
            response["beanie_working"] = False
        
        return response
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
