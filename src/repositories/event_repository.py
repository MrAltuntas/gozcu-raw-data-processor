"""Event repository for camera events raw data."""

import logging
from typing import List

from asyncpg.exceptions import PostgresError

from src.core.database import db_manager
from src.models.camera_event import CameraEventRaw

logger = logging.getLogger(__name__)


class EventRepository:
    """Repository for managing camera events raw data in TimescaleDB."""

    async def bulk_insert(self, events: List[CameraEventRaw]) -> int:
        """
        Bulk insert camera events using COPY command for optimal performance.

        Args:
            events: List of CameraEventRaw objects to insert

        Returns:
            Number of successfully inserted records

        Raises:
            RuntimeError: If database pool is not initialized
            PostgresError: If database operation fails
        """
        if not events:
            logger.warning("No events to insert")
            return 0

        inserted_count = 0

        try:
            async with db_manager.get_connection() as conn:
                # Prepare data for COPY command
                # COPY expects tuples in the same order as table columns
                records = [
                    (
                        event.camera_id,
                        event.event_time,
                        event.frame_number,
                        event.has_detection,
                        event.detection_count,
                        event.processing_time_ms,
                        event.stream_lag_ms,
                    )
                    for event in events
                ]

                # Use COPY command for bulk insert - much faster than executemany
                inserted_count = await conn.copy_records_to_table(
                    table_name="camera_events_raw",
                    records=records,
                    columns=[
                        "camera_id",
                        "event_time",
                        "frame_number",
                        "has_detection",
                        "detection_count",
                        "processing_time_ms",
                        "stream_lag_ms",
                    ],
                )

                logger.info(f"Successfully inserted {inserted_count} camera events")
                return inserted_count

        except PostgresError as e:
            logger.error(
                f"Database error during bulk insert: {e.sqlstate} - {e.message}"
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error during bulk insert: {e}")
            raise RuntimeError(f"Failed to insert camera events: {e}") from e


# Singleton instance
event_repository = EventRepository()