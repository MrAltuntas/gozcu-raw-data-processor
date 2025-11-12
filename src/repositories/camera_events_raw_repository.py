"""Camera events raw repository for JSONB data."""

import json
import logging
from typing import List

from asyncpg.exceptions import PostgresError

from src.core.database import db_manager
from database.models.camera_events_raw import CameraEventRaw

logger = logging.getLogger(__name__)


class CameraEventsRawRepository:
    """Repository for managing camera events raw JSONB data in TimescaleDB."""

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
                # Convert event_data dict to JSON string for JSONB column
                records = [
                    (
                        event.camera_id,
                        event.event_time,
                        json.dumps(event.event_data) if isinstance(event.event_data, dict) else event.event_data,
                    )
                    for event in events
                ]

                # Use COPY command for bulk insert - much faster than executemany
                copy_result = await conn.copy_records_to_table(
                    table_name="camera_events_raw",
                    records=records,
                    columns=[
                        "camera_id",
                        "event_time",
                        "event_data",
                    ],
                )

                # Extract numeric count from COPY command result (e.g., "COPY 123" -> 123)
                if isinstance(copy_result, str) and copy_result.startswith("COPY "):
                    inserted_count = int(copy_result.split()[1])
                else:
                    inserted_count = int(copy_result)

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
camera_events_raw_repository = CameraEventsRawRepository()