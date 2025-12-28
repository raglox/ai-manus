from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError as RedisTimeoutError
import logging
import asyncio
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._client: Redis | None = None
        self._settings = get_settings()
    
    async def initialize(self, max_retries: int = 5, retry_delay: float = 2.0) -> None:
        """Initialize Redis connection with retry logic and proper timeouts.
        
        Args:
            max_retries: Maximum number of connection attempts (default: 5)
            retry_delay: Delay between retries in seconds (default: 2.0)
        """
        if self._client is not None:
            return
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting to connect to Redis (attempt {attempt}/{max_retries})...")
                
                # Redis connection with better timeout settings
                redis_password = self._settings.redis_password
                # Handle "no-password" special case
                if redis_password and redis_password.lower() in ["no-password", "none", ""]:
                    redis_password = None
                
                self._client = Redis(
                    host=self._settings.redis_host,
                    port=self._settings.redis_port,
                    db=self._settings.redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=30,  # 30 seconds connection timeout
                    socket_timeout=30,  # 30 seconds socket timeout
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 1,  # TCP_KEEPINTVL
                        3: 3,  # TCP_KEEPCNT
                    },
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                
                # Verify the connection with timeout
                await asyncio.wait_for(
                    self._client.ping(),
                    timeout=10.0
                )
                
                logger.info(f"✅ Successfully connected to Redis on attempt {attempt}")
                logger.info(f"Redis host: {self._settings.redis_host}:{self._settings.redis_port}")
                return
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"Redis connection timeout on attempt {attempt}/{max_retries}")
            except (ConnectionError, RedisTimeoutError) as e:
                last_error = e
                logger.warning(f"Redis connection failed on attempt {attempt}/{max_retries}: {str(e)}")
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected error on attempt {attempt}/{max_retries}: {str(e)}")
            
            # Clean up failed client
            if self._client is not None:
                try:
                    await self._client.close()
                except:
                    pass
                self._client = None
            
            # Wait before retrying (exponential backoff)
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        # If all retries failed, raise the last error
        error_msg = f"Failed to connect to Redis after {max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    async def shutdown(self) -> None:
        """Shutdown Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")
                # Clear cache for this module
        get_redis.cache_clear()
    
    @property
    def client(self) -> Redis:
        """Return initialized Redis client - auto-initialize if needed"""
        if self._client is None:
            logger.warning("⚠️ Redis accessed before initialization - returning None")
            logger.warning("⚠️ Application running in degraded mode without Redis")
        return self._client

from functools import lru_cache

@lru_cache()
def get_redis() -> RedisClient:
    """Get the Redis client instance."""
    return RedisClient() 