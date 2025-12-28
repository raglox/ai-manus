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


# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup
    logger.info("="*80)
    logger.info("🚀 Application startup - Manus AI Agent initializing")
    logger.info("="*80)
    
    # Initialize flags
    mongodb_initialized = False
    redis_initialized = False
    
    # Store initial state (will be updated by background task)
    app.state.mongodb_initialized = False
    app.state.redis_initialized = False
    app.state.startup_complete = False
    
    # Create background task for DB initialization
    async def initialize_databases():
        nonlocal mongodb_initialized, redis_initialized
        
        # MongoDB initialization with extended timeout (120 seconds total)
        try:
            logger.info("📊 Starting MongoDB connection...")
            await asyncio.wait_for(
                get_mongodb().initialize(max_retries=5, retry_delay=3.0),
                timeout=120.0  # 120 seconds total timeout
            )
            
            logger.info("📊 Initializing Beanie ODM...")
            await asyncio.wait_for(
                init_beanie(
                    database=get_mongodb().client[settings.mongodb_database],
                    document_models=[AgentDocument, SessionDocument, UserDocument, SubscriptionDocument]
                ),
                timeout=30.0  # 30 seconds for Beanie initialization
            )
            
            mongodb_initialized = True
            app.state.mongodb_initialized = True
            logger.info("✅ Successfully initialized MongoDB and Beanie")
            logger.info(f"   Database: {settings.mongodb_database}")
            
        except asyncio.TimeoutError:
            logger.error("❌ MongoDB initialization timed out after 120 seconds")
            logger.warning("⚠️ Application will run in degraded mode without MongoDB")
        except Exception as e:
            logger.error(f"❌ MongoDB initialization failed: {str(e)}")
            logger.warning("⚠️ Application will run in degraded mode without MongoDB")
            # Log more details for debugging
            import traceback
            logger.debug(f"MongoDB error traceback:\n{traceback.format_exc()}")
        
        # Redis initialization with extended timeout (60 seconds total)
        try:
            logger.info("🔴 Starting Redis connection...")
            await asyncio.wait_for(
                get_redis().initialize(max_retries=5, retry_delay=2.0),
                timeout=60.0  # 60 seconds total timeout
            )
            
            redis_initialized = True
            app.state.redis_initialized = True
            logger.info("✅ Successfully initialized Redis")
            logger.info(f"   Host: {settings.redis_host}:{settings.redis_port}")
            
        except asyncio.TimeoutError:
            logger.error("❌ Redis initialization timed out after 60 seconds")
            logger.warning("⚠️ Application will run in degraded mode without Redis caching")
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {str(e)}")
            logger.warning("⚠️ Application will run in degraded mode without Redis caching")
            # Log more details for debugging
            import traceback
            logger.debug(f"Redis error traceback:\n{traceback.format_exc()}")
        
        # Startup summary
        logger.info("="*80)
        logger.info("🎯 Startup Summary:")
        logger.info(f"   MongoDB: {'✅ Connected' if mongodb_initialized else '❌ Disconnected (degraded mode)'}")
        logger.info(f"   Redis:   {'✅ Connected' if redis_initialized else '❌ Disconnected (degraded mode)'}")
        logger.info("="*80)
        
        app.state.startup_complete = True
    
    # Start DB initialization in background
    logger.info("⚡ Starting database initialization in background...")
    logger.info("🌐 Application will be ready to serve traffic immediately")
    asyncio.create_task(initialize_databases())
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("="*80)
        logger.info("🛑 Application shutdown - Manus AI Agent terminating")
        logger.info("="*80)
        
        # Get actual initialization status
        mongodb_initialized = app.state.mongodb_initialized
        redis_initialized = app.state.redis_initialized
        
        # Disconnect from MongoDB
        if mongodb_initialized:
            try:
                logger.info("Disconnecting from MongoDB...")
                await asyncio.wait_for(get_mongodb().shutdown(), timeout=10.0)
                logger.info("✅ MongoDB disconnected successfully")
            except asyncio.TimeoutError:
                logger.warning("⚠️ MongoDB shutdown timed out")
            except Exception as e:
                logger.error(f"❌ Error shutting down MongoDB: {e}")
        
        # Disconnect from Redis
        if redis_initialized:
            try:
                logger.info("Disconnecting from Redis...")
                await asyncio.wait_for(get_redis().shutdown(), timeout=10.0)
                logger.info("✅ Redis disconnected successfully")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Redis shutdown timed out")
            except Exception as e:
                logger.error(f"❌ Error shutting down Redis: {e}")

        logger.info("Cleaning up AgentService instance...")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("✅ AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("⚠️ AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"❌ Error during AgentService cleanup: {str(e)}")
        
        logger.info("="*80)
        logger.info("👋 Shutdown complete. Goodbye!")
        logger.info("="*80)
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("="*80)
        logger.info("🛑 Application shutdown - Manus AI Agent terminating")
        logger.info("="*80)
        
        # Disconnect from MongoDB
        if mongodb_initialized:
            try:
                logger.info("Disconnecting from MongoDB...")
                await asyncio.wait_for(get_mongodb().shutdown(), timeout=10.0)
                logger.info("✅ MongoDB disconnected successfully")
            except asyncio.TimeoutError:
                logger.warning("⚠️ MongoDB shutdown timed out")
            except Exception as e:
                logger.error(f"❌ Error shutting down MongoDB: {e}")
        
        # Disconnect from Redis
        if redis_initialized:
            try:
                logger.info("Disconnecting from Redis...")
                await asyncio.wait_for(get_redis().shutdown(), timeout=10.0)
                logger.info("✅ Redis disconnected successfully")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Redis shutdown timed out")
            except Exception as e:
                logger.error(f"❌ Error shutting down Redis: {e}")

        logger.info("Cleaning up AgentService instance...")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("✅ AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("⚠️ AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"❌ Error during AgentService cleanup: {str(e)}")
        
        logger.info("="*80)
        logger.info("👋 Shutdown complete. Goodbye!")
        logger.info("="*80)

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