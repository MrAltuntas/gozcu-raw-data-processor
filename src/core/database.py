"""TimescaleDB database client implementation"""
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """PostgreSQL connection pool manager using asyncpg"""

    def __init__(self):
        """Initialize database manager"""
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Create and initialize connection pool"""
        if self._pool is not None:
            logger.warning("Database pool already exists")
            return

        try:
            logger.info(
                f"Connecting to database at {settings.database.host}:{settings.database.port}"
            )

            self._pool = await asyncpg.create_pool(
                host=settings.database.host,
                port=settings.database.port,
                database=settings.database.database,
                user=settings.database.user,
                password=settings.database.password,
                min_size=1,
                max_size=settings.database.pool_size,
                command_timeout=60,
            )

            logger.info(
                f"Database pool created successfully (pool_size={settings.database.pool_size})"
            )

        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close and cleanup connection pool"""
        if self._pool is None:
            logger.warning("Database pool does not exist")
            return

        try:
            logger.info("Closing database pool")
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed successfully")

        except Exception as e:
            logger.error(f"Failed to close database pool: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection from the pool (async context manager)

        Usage:
            async with db_manager.get_connection() as conn:
                result = await conn.fetch("SELECT * FROM table")
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        """Get the connection pool instance"""
        return self._pool

    @property
    def is_connected(self) -> bool:
        """Check if pool is connected"""
        return self._pool is not None


# Singleton instance
db_manager = DatabaseManager()
