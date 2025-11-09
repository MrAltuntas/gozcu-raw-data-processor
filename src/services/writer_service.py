"""Writer service - Main orchestrator for Redis to DB pipeline"""
import asyncio
import logging
import time
from typing import Optional

from src.config.settings import settings
from src.repositories.detection_repository import detection_repository
from src.repositories.event_repository import event_repository
from src.services.batch_processor import batch_processor
from src.services.redis_consumer import redis_consumer

logger = logging.getLogger(__name__)


class WriterService:
    """
    Main orchestrator service for processing camera events from Redis to Database.

    Workflow:
    1. Read batch from Redis stream
    2. Process and validate batch
    3. Bulk insert events to TimescaleDB
    4. Bulk insert detections to TimescaleDB
    5. Acknowledge messages in Redis
    6. Log metrics and repeat
    """

    def __init__(self):
        """Initialize WriterService with all required dependencies"""
        self._redis_consumer = redis_consumer
        self._batch_processor = batch_processor
        self._event_repo = event_repository
        self._detection_repo = detection_repository

        self._running = False
        self._shutdown_event = asyncio.Event()

        # Configuration from settings
        self._batch_size = settings.processing.batch_size
        self._batch_timeout_ms = int(settings.processing.batch_timeout_seconds * 1000)
        self._max_retries = settings.processing.max_retries

    async def _process_single_batch(self) -> dict:
        """
        Process a single batch of messages from Redis.

        Returns:
            dict: Metrics about the processing (events_count, detections_count, duration_ms)

        Raises:
            Exception: If processing fails after all retries
        """
        start_time = time.time()

        # 1. Read batch from Redis stream
        raw_messages = await self._redis_consumer.read_stream(
            count=self._batch_size,
            block_ms=self._batch_timeout_ms
        )

        if not raw_messages:
            return {
                "events_count": 0,
                "detections_count": 0,
                "messages_count": 0,
                "duration_ms": 0
            }

        message_ids = [msg["id"] for msg in raw_messages]

        try:
            # 2. Process batch (parse and validate)
            events, detections = await self._batch_processor.process_batch(raw_messages)

            # 3. Bulk insert events
            events_inserted = 0
            if events:
                events_inserted = await self._event_repo.bulk_insert(events)

            # 4. Bulk insert detections
            detections_inserted = 0
            if detections:
                detections_inserted = await self._detection_repo.bulk_insert(detections)

            # 5. Acknowledge messages in Redis
            ack_count = await self._redis_consumer.acknowledge(message_ids)

            duration_ms = int((time.time() - start_time) * 1000)

            # 6. Return metrics
            return {
                "events_count": events_inserted,
                "detections_count": detections_inserted,
                "messages_count": len(raw_messages),
                "ack_count": ack_count,
                "duration_ms": duration_ms
            }

        except Exception as e:
            logger.error(
                f"Error processing batch of {len(raw_messages)} messages: {e}",
                exc_info=True
            )
            # Don't acknowledge failed messages - they will be retried
            raise

    async def _process_with_retry(self) -> Optional[dict]:
        """
        Process batch with retry logic.

        Returns:
            dict: Processing metrics or None if all retries failed
        """
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                metrics = await self._process_single_batch()

                # Log successful processing
                if metrics["messages_count"] > 0:
                    logger.info(
                        f"Batch processed successfully: "
                        f"{metrics['messages_count']} messages, "
                        f"{metrics['events_count']} events, "
                        f"{metrics['detections_count']} detections "
                        f"in {metrics['duration_ms']}ms"
                    )

                return metrics

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Batch processing attempt {attempt}/{self._max_retries} failed: {e}"
                )

                if attempt < self._max_retries:
                    # Exponential backoff
                    backoff_seconds = 2 ** attempt
                    logger.info(f"Retrying in {backoff_seconds} seconds...")
                    await asyncio.sleep(backoff_seconds)

        # All retries failed
        logger.error(
            f"Batch processing failed after {self._max_retries} attempts. "
            f"Last error: {last_error}",
            exc_info=last_error
        )
        return None

    async def start(self) -> None:
        """
        Start the writer service main loop.

        This method runs indefinitely until stop() is called.
        It continuously reads from Redis, processes batches, and writes to database.

        Raises:
            RuntimeError: If service is already running
        """
        if self._running:
            raise RuntimeError("WriterService is already running")

        logger.info("Starting WriterService...")

        try:
            # Initialize Redis consumer
            await self._redis_consumer.initialize()

            self._running = True
            self._shutdown_event.clear()

            logger.info(
                f"WriterService started successfully "
                f"(batch_size={self._batch_size}, "
                f"timeout={self._batch_timeout_ms}ms, "
                f"max_retries={self._max_retries})"
            )

            # Statistics
            total_messages = 0
            total_events = 0
            total_detections = 0
            batch_count = 0

            # Main processing loop
            while self._running:
                try:
                    # Check for shutdown signal
                    if self._shutdown_event.is_set():
                        logger.info("Shutdown signal received, stopping...")
                        break

                    # Process batch with retry logic
                    metrics = await self._process_with_retry()

                    if metrics:
                        total_messages += metrics.get("messages_count", 0)
                        total_events += metrics.get("events_count", 0)
                        total_detections += metrics.get("detections_count", 0)
                        batch_count += 1

                        # Log aggregate statistics periodically
                        if batch_count % 10 == 0:
                            logger.info(
                                f"Aggregate stats: {batch_count} batches, "
                                f"{total_messages} messages, "
                                f"{total_events} events, "
                                f"{total_detections} detections processed"
                            )

                    # Small delay to prevent tight loop on empty batches
                    if metrics and metrics.get("messages_count", 0) == 0:
                        await asyncio.sleep(1)

                except asyncio.CancelledError:
                    logger.info("WriterService task cancelled")
                    break

                except Exception as e:
                    logger.error(
                        f"Unexpected error in main loop: {e}",
                        exc_info=True
                    )
                    # Continue running, but add delay to prevent error spam
                    await asyncio.sleep(5)

            logger.info(
                f"WriterService stopped. Final stats: "
                f"{batch_count} batches, "
                f"{total_messages} messages, "
                f"{total_events} events, "
                f"{total_detections} detections"
            )

        except Exception as e:
            logger.error(f"Critical error in WriterService: {e}", exc_info=True)
            raise

        finally:
            self._running = False

    async def stop(self) -> None:
        """
        Gracefully stop the writer service.

        Signals the main loop to stop and waits for current batch to complete.
        """
        if not self._running:
            logger.warning("WriterService is not running")
            return

        logger.info("Stopping WriterService gracefully...")

        # Signal shutdown
        self._running = False
        self._shutdown_event.set()

        # Give some time for current batch to complete
        await asyncio.sleep(2)

        logger.info("WriterService stopped")

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running"""
        return self._running

    async def get_status(self) -> dict:
        """
        Get current status of the writer service.

        Returns:
            dict: Service status including pending messages count
        """
        pending_info = await self._redis_consumer.get_pending_info()

        return {
            "running": self._running,
            "batch_size": self._batch_size,
            "batch_timeout_ms": self._batch_timeout_ms,
            "max_retries": self._max_retries,
            "pending_messages": pending_info.get("local_pending_count", 0),
            "redis_pending_messages": pending_info.get("count", 0)
        }


# Singleton instance
writer_service = WriterService()
