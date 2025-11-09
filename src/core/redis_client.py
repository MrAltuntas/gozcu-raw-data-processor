"""Redis client implementation"""
import redis.asyncio as redis
from typing import Optional
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager using redis-py async client"""

    def __init__(self):
        """Initialize Redis manager"""
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Create and initialize Redis client"""
        if self._client is not None:
            logger.warning("Redis client already exists")
            return

        try:
            logger.info(
                f"Connecting to Redis at {settings.redis.host}:{settings.redis.port}"
            )

            self._client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            # Test connection
            await self._client.ping()

            logger.info("Redis client connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
            raise

    async def disconnect(self) -> None:
        """Close and cleanup Redis connection"""
        if self._client is None:
            logger.warning("Redis client does not exist")
            return

        try:
            logger.info("Closing Redis connection")
            await self._client.aclose()
            self._client = None
            logger.info("Redis connection closed successfully")

        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")
            raise

    def get_client(self) -> redis.Redis:
        """
        Get the Redis client instance

        Returns:
            redis.Redis: The Redis client

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis client is connected"""
        return self._client is not None


# Singleton instance
redis_manager = RedisManager()
