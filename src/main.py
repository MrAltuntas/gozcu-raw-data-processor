"""Main application entry point"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.core.database import db_manager
from src.core.redis_client import redis_manager
from src.services.writer_service import writer_service

logger = logging.getLogger(__name__)


class Application:
    """Main application orchestrator with lifecycle management"""

    def __init__(self):
        """Initialize application"""
        self._shutdown_event: Optional[asyncio.Event] = None
        self._writer_task: Optional[asyncio.Task] = None

    async def startup(self) -> None:
        """
        Initialize all application components.

        Order:
        1. Database connection
        2. Redis connection
        3. Service initialization
        """
        logger.info("Starting application initialization...")

        try:
            # 1. Connect to TimescaleDB
            logger.info("Initializing database connection...")
            await db_manager.connect()
            logger.info("Database connected successfully")

            # 2. Connect to Redis
            logger.info("Initializing Redis connection...")
            await redis_manager.connect()
            logger.info("Redis connected successfully")

            logger.info("Application initialization completed")

        except Exception as e:
            logger.error(f"Application startup failed: {e}", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """
        Gracefully shutdown all application components.

        Order:
        1. Stop writer service
        2. Close Redis connection
        3. Close database connection
        """
        logger.info("Starting graceful shutdown...")

        try:
            # 1. Stop writer service
            if writer_service.is_running:
                logger.info("Stopping writer service...")
                await writer_service.stop()

            # 2. Cancel writer task if running
            if self._writer_task and not self._writer_task.done():
                logger.info("Cancelling writer task...")
                self._writer_task.cancel()
                try:
                    await self._writer_task
                except asyncio.CancelledError:
                    logger.info("Writer task cancelled")

            # 3. Close Redis connection
            if redis_manager.is_connected:
                logger.info("Closing Redis connection...")
                await redis_manager.disconnect()

            # 4. Close database connection
            if db_manager.is_connected:
                logger.info("Closing database connection...")
                await db_manager.disconnect()

            logger.info("Graceful shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    async def run(self) -> None:
        """
        Main application run loop.

        Starts the writer service and waits for shutdown signal.
        """
        self._shutdown_event = asyncio.Event()

        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()

        def signal_handler():
            """Handle shutdown signals"""
            logger.info("Received shutdown signal")
            self._shutdown_event.set()

        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        try:
            # Start writer service in background task
            logger.info("Starting writer service...")
            self._writer_task = asyncio.create_task(writer_service.start())

            # Wait for shutdown signal
            logger.info("Application is running. Press Ctrl+C to stop.")
            await self._shutdown_event.wait()

            # Graceful shutdown
            await self.shutdown()

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            await self.shutdown()
            raise


async def main() -> None:
    """
    Main entry point for the application.

    Steps:
    1. Setup logging
    2. Initialize application components
    3. Start writer service
    4. Handle graceful shutdown on SIGINT/SIGTERM
    """
    # 1. Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("Gozcu Raw Data Processor")
    logger.info("=" * 60)
    logger.info(f"Database: {settings.database.host}:{settings.database.port}/{settings.database.database}")
    logger.info(f"Redis: {settings.redis.host}:{settings.redis.port}")
    logger.info(f"Stream Key: {settings.redis.stream_key}")
    logger.info(f"Consumer Group: {settings.redis.consumer_group}")
    logger.info(f"Consumer Name: {settings.redis.consumer_name}")
    logger.info(f"Batch Size: {settings.processing.batch_size}")
    logger.info(f"Batch Timeout: {settings.processing.batch_timeout_seconds}s")
    logger.info(f"Max Retries: {settings.processing.max_retries}")
    logger.info("=" * 60)

    app = Application()

    try:
        # 2. Initialize all components
        await app.startup()

        # 3. Run main loop
        await app.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await app.shutdown()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await app.shutdown()
        sys.exit(1)

    logger.info("Application exited successfully")


if __name__ == "__main__":
    """
    Entry point when running as a script.

    Usage:
        python -m src.main
        or
        python src/main.py
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
