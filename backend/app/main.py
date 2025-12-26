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

# Initialize Redis-backed Rate Limiter
redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
if settings.redis_password:
    redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

limiter = create_rate_limiter(redis_url)
logger.info(f"Rate limiter initialized with Redis backend: {settings.redis_host}:{settings.redis_port}")


# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup
    logger.info("Application startup - Manus AI Agent initializing")
    
    # Initialize MongoDB and Beanie
    await get_mongodb().initialize()

    # Initialize Beanie
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument, SubscriptionDocument]
    )
    logger.info("Successfully initialized Beanie")
    
    # Initialize Redis
    await get_redis().initialize()
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("Application shutdown - Manus AI Agent terminating")
        # Disconnect from MongoDB
        await get_mongodb().shutdown()
        # Disconnect from Redis
        await get_redis().shutdown()


        logger.info("Cleaning up AgentService instance")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error during AgentService cleanup: {str(e)}")

app = FastAPI(title="Manus AI Agent", lifespan=lifespan)

# Attach limiter to app for SlowAPI
app.state.limiter = limiter

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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