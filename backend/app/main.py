from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import asyncio
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.interfaces.dependencies import get_agent_service
from app.interfaces.api.routes import router
from app.infrastructure.logging import setup_logging
from app.interfaces.errors.exception_handlers import register_exception_handlers
from app.infrastructure.models.documents import AgentDocument, SessionDocument, UserDocument, SubscriptionDocument
from app.infrastructure.middleware import BillingMiddleware
from app.infrastructure.middleware.rate_limit import SimpleRateLimiter
from app.infrastructure.middleware.advanced_rate_limit import create_rate_limiter, get_rate_limit
from app.infrastructure.middleware.cors_handler import CORSHeaderMiddleware
from app.infrastructure.repositories.subscription_repository import MongoSubscriptionRepository
from beanie import init_beanie
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

# Initialize logging system
setup_logging()
logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()

# Initialize Sentry for error tracking and performance monitoring
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(transaction_style="url"),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        environment=settings.sentry_environment,
        # Set release version from environment or default
        release=f"manus-backend@{settings.sentry_environment}",
        # Send PII (Personally Identifiable Information) - set to False in production
        send_default_pii=False,
        # Before send hook to filter sensitive data
        before_send=lambda event, hint: event,  # Can add filtering logic here
    )
    logger.info(f"✅ Sentry initialized for environment: {settings.sentry_environment}")
else:
    logger.warning("⚠️ Sentry DSN not configured - error tracking disabled")

# Initialize Redis-backed Rate Limiter (with graceful failure)
try:
    redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    if settings.redis_password and settings.redis_password != "no-password":
        redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    
    limiter = create_rate_limiter(redis_url)
    logger.info(f"✅ Rate limiter initialized with Redis backend: {settings.redis_host}:{settings.redis_port}")
except Exception as e:
    logger.warning(f"⚠️ Rate limiter initialization failed: {e}. Using memory-based rate limiter.")
    # Fallback to memory-based rate limiter
    limiter = Limiter(key_func=lambda: "global", default_limits=["1000/hour"])


# Create lifespan context manager - NO DB INITIALIZATION
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - handles startup and shutdown.
    DB initialization is LAZY - happens on first use to allow immediate port binding.
    """
    # Code executed on startup
    logger.info("="*80)
    logger.info("🚀 Application startup - Manus AI Backend")
    logger.info("="*80)
    logger.info("⚡ Port binding immediately - DBs will connect on first use")
    logger.info("="*80)
    
    # Initialize state flags
    app.state.mongodb_initialized = False
    app.state.redis_initialized = False
    app.state.startup_complete = True  # Mark as complete immediately
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("="*80)
        logger.info("🛑 Application shutdown - Manus AI Backend")
        logger.info("="*80)
        
        # Disconnect from MongoDB if it was initialized
        try:
            mongodb = get_mongodb()
            if mongodb._client is not None:
                logger.info("Disconnecting from MongoDB...")
                await asyncio.wait_for(mongodb.shutdown(), timeout=10.0)
                logger.info("✅ MongoDB disconnected successfully")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB shutdown issue: {e}")
        
        # Disconnect from Redis if it was initialized
        try:
            redis = get_redis()
            if redis._redis is not None:
                logger.info("Disconnecting from Redis...")
                await asyncio.wait_for(redis.shutdown(), timeout=10.0)
                logger.info("✅ Redis disconnected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis shutdown issue: {e}")

        # Shutdown AgentService
        try:
            logger.info("Cleaning up AgentService...")
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("✅ AgentService shutdown completed")
        except Exception as e:
            logger.warning(f"⚠️ AgentService shutdown issue: {e}")
        
        logger.info("="*80)
        logger.info("👋 Shutdown complete")
        logger.info("="*80)

app = FastAPI(title="Manus AI Agent", lifespan=lifespan)

# Attach limiter to app for SlowAPI
app.state.limiter = limiter

# Add CORS Header Middleware (MUST be first to catch all responses including errors)
app.add_middleware(
    CORSHeaderMiddleware,
    allowed_origins=[
        "http://34.121.111.2",
        "http://localhost:5173",
        "http://localhost:3000",
    ]
)

# Configure CORS - Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://34.121.111.2",
        "http://localhost:5173",
        "http://localhost:3000",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add Rate Limiting Middleware (for webhook protection)
app.add_middleware(
    SimpleRateLimiter,
    requests_per_minute=100  # 100 requests per minute per IP
)

# DISABLED: Add Billing Middleware for subscription enforcement
# TODO: Fix user_id extraction before enabling
# app.add_middleware(
#     BillingMiddleware,
#     subscription_repository=MongoSubscriptionRepository()
# )

# Register exception handlers
register_exception_handlers(app)

# Register rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    logger.warning(f"Rate limit exceeded for {request.client.host} on {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail if hasattr(exc, 'detail') else "60 seconds"
        }
    )

# Register routes
app.include_router(router, prefix="/api/v1")
