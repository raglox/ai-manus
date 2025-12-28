#!/usr/bin/env python3
"""
Database Connection Health Check Script
This script verifies MongoDB and Redis connections before starting the application.
Usage: python check_connections.py
"""

import asyncio
import sys
import os
from typing import Tuple

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.core.config import get_settings
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_mongodb() -> Tuple[bool, str]:
    """Check MongoDB connection.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info("🔍 Checking MongoDB connection...")
        settings = get_settings()
        
        # Try to initialize with 3 retries
        await get_mongodb().initialize(max_retries=3, retry_delay=2.0)
        
        # Try a simple operation
        client = get_mongodb().client
        await client.admin.command('ping')
        
        logger.info("✅ MongoDB connection successful!")
        return True, "MongoDB is accessible"
        
    except Exception as e:
        error_msg = f"MongoDB connection failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


async def check_redis() -> Tuple[bool, str]:
    """Check Redis connection.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info("🔍 Checking Redis connection...")
        settings = get_settings()
        
        # Try to initialize with 3 retries
        await get_redis().initialize(max_retries=3, retry_delay=2.0)
        
        # Try a simple operation
        client = get_redis().client
        await client.ping()
        
        logger.info("✅ Redis connection successful!")
        return True, "Redis is accessible"
        
    except Exception as e:
        error_msg = f"Redis connection failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


async def main():
    """Main health check routine."""
    logger.info("="*80)
    logger.info("🏥 Starting Database Health Checks")
    logger.info("="*80)
    
    # Check MongoDB
    mongodb_ok, mongodb_msg = await check_mongodb()
    
    # Check Redis
    redis_ok, redis_msg = await check_redis()
    
    # Print summary
    logger.info("="*80)
    logger.info("📊 Health Check Summary:")
    logger.info(f"   MongoDB: {'✅ OK' if mongodb_ok else '❌ FAILED'} - {mongodb_msg}")
    logger.info(f"   Redis:   {'✅ OK' if redis_ok else '❌ FAILED'} - {redis_msg}")
    logger.info("="*80)
    
    # Cleanup
    if mongodb_ok:
        try:
            await get_mongodb().shutdown()
        except:
            pass
    
    if redis_ok:
        try:
            await get_redis().shutdown()
        except:
            pass
    
    # Exit with appropriate code
    if mongodb_ok and redis_ok:
        logger.info("✅ All health checks passed!")
        sys.exit(0)
    elif mongodb_ok or redis_ok:
        logger.warning("⚠️ Some health checks failed - application will run in degraded mode")
        sys.exit(0)  # Don't fail - let app start in degraded mode
    else:
        logger.error("❌ All health checks failed!")
        logger.error("💡 Tip: Check your MONGODB_URI and REDIS_HOST environment variables")
        sys.exit(1)  # Fail if both are down


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during health check: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
