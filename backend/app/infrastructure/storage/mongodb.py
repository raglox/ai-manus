from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging
import asyncio
from app.core.config import get_settings
from functools import lru_cache
from beanie import init_beanie

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._settings = get_settings()
        self._beanie_initialized = False
    
    async def initialize(self, max_retries: int = 5, retry_delay: float = 2.0) -> None:
        """Initialize MongoDB connection with retry logic and proper timeouts.
        
        Args:
            max_retries: Maximum number of connection attempts (default: 5)
            retry_delay: Delay between retries in seconds (default: 2.0)
        """
        if self._client is not None and self._beanie_initialized:
            return
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {attempt}/{max_retries})...")
                
                # MongoDB connection options for better timeout handling
                connection_options = {
                    'serverSelectionTimeoutMS': 30000,  # 30 seconds
                    'connectTimeoutMS': 30000,  # 30 seconds
                    'socketTimeoutMS': 60000,  # 60 seconds
                    'maxPoolSize': 50,
                    'minPoolSize': 10,
                    'retryWrites': True,
                    'retryReads': True,
                }
                
                # Connect to MongoDB
                if self._settings.mongodb_username and self._settings.mongodb_password:
                    # Use authenticated connection if username and password are configured
                    self._client = AsyncIOMotorClient(
                        self._settings.mongodb_uri,
                        username=self._settings.mongodb_username,
                        password=self._settings.mongodb_password,
                        **connection_options
                    )
                else:
                    # Use unauthenticated connection if no credentials are provided
                    self._client = AsyncIOMotorClient(
                        self._settings.mongodb_uri,
                        **connection_options
                    )
                
                # Verify the connection with timeout
                await asyncio.wait_for(
                    self._client.admin.command('ping'),
                    timeout=30.0
                )
                
                logger.info(f"✅ Successfully connected to MongoDB on attempt {attempt}")
                logger.info(f"MongoDB URI: {self._settings.mongodb_uri[:20]}...")
                
                # Initialize Beanie ODM
                if not self._beanie_initialized:
                    logger.info("🔧 Initializing Beanie ODM...")
                    from app.infrastructure.models.documents import (
                        AgentDocument, SessionDocument, UserDocument, SubscriptionDocument
                    )
                    
                    database = self._client[self._settings.mongodb_database]
                    await init_beanie(
                        database=database,
                        document_models=[
                            AgentDocument,
                            SessionDocument,
                            UserDocument,
                            SubscriptionDocument
                        ]
                    )
                    self._beanie_initialized = True
                    logger.info(f"✅ Beanie ODM initialized with database: {self._settings.mongodb_database}")
                
                return
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"MongoDB connection timeout on attempt {attempt}/{max_retries}")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                last_error = e
                logger.warning(f"MongoDB connection failed on attempt {attempt}/{max_retries}: {str(e)}")
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected error on attempt {attempt}/{max_retries}: {str(e)}")
            
            # Wait before retrying (exponential backoff)
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        # If all retries failed, raise the last error
        error_msg = f"Failed to connect to MongoDB after {max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)
    
    async def shutdown(self) -> None:
        """Shutdown MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Disconnected from MongoDB")
                # Clear cache for this module
        get_mongodb.cache_clear()
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Return initialized MongoDB client - auto-initialize if needed"""
        if self._client is None:
            logger.warning("⚠️ MongoDB accessed before initialization - returning None")
            logger.warning("⚠️ Application running in degraded mode without MongoDB")
        return self._client
    
    @property
    def is_beanie_initialized(self) -> bool:
        """Check if Beanie is initialized"""
        return self._beanie_initialized


@lru_cache()
def get_mongodb() -> MongoDB:
    """Get the MongoDB instance."""
    return MongoDB()

