"""Detection repository for camera detections raw data."""

import logging
from typing import List

from asyncpg.exceptions import PostgresError

from src.core.database import db_manager
from src.models.detection import CameraDetectionRaw

logger = logging.getLogger(__name__)


class DetectionRepository:
    """Repository for managing camera detections raw data in TimescaleDB."""

    async def bulk_insert(self, detections: List[CameraDetectionRaw]) -> int:
        """
        Bulk insert camera detections using COPY command for optimal performance.

        Args:
            detections: List of CameraDetectionRaw objects to insert

        Returns:
            Number of successfully inserted records

        Raises:
            RuntimeError: If database pool is not initialized
            PostgresError: If database operation fails
        """
        if not detections:
            logger.warning("No detections to insert")
            return 0

        inserted_count = 0

        try:
            async with db_manager.get_connection() as conn:
                # Prepare data for COPY command
                # COPY expects tuples in the same order as table columns
                records = [
                    (
                        detection.event_time,
                        detection.camera_id,
                        detection.class_id,
                        detection.confidence,
                        detection.photo_url,
                        detection.coord_x,
                        detection.coord_y,
                        detection.region_ids,
                        detection.bbox_width,
                        detection.bbox_height,
                        detection.object_id,
                        detection.track_id,
                    )
                    for detection in detections
                ]

                # Use COPY command for bulk insert - much faster than executemany
                inserted_count = await conn.copy_records_to_table(
                    table_name="camera_detections_raw",
                    records=records,
                    columns=[
                        "event_time",
                        "camera_id",
                        "class_id",
                        "confidence",
                        "photo_url",
                        "coord_x",
                        "coord_y",
                        "region_ids",
                        "bbox_width",
                        "bbox_height",
                        "object_id",
                        "track_id",
                    ],
                )

                logger.info(f"Successfully inserted {inserted_count} camera detections")
                return inserted_count

        except PostgresError as e:
            logger.error(
                f"Database error during bulk insert: {e.sqlstate} - {e.message}"
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error during bulk insert: {e}")
            raise RuntimeError(f"Failed to insert camera detections: {e}") from e


# Singleton instance
detection_repository = DetectionRepository()