"""Batch processing service"""
import json
import logging
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from src.models.camera_event import CameraEventRaw
from src.models.detection import CameraDetectionRaw

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process batches of raw messages from Redis stream"""

    @staticmethod
    def _parse_datetime(value: str | datetime) -> Optional[datetime]:
        """
        Parse datetime from string or return as-is if already datetime

        Args:
            value: Datetime string or datetime object

        Returns:
            datetime object or None if parsing fails
        """
        if isinstance(value, datetime):
            return value

        if not value:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                # Try common timestamp formats
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.warning(f"Failed to parse datetime: {value}")
                return None

    @staticmethod
    def _parse_region_ids(value: str | list | None) -> Optional[list[int]]:
        """
        Parse region_ids from string or list

        Args:
            value: JSON string, list, or None

        Returns:
            List of integers or None
        """
        if value is None or value == "":
            return None

        if isinstance(value, list):
            return [int(x) for x in value]

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [int(x) for x in parsed]
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"Failed to parse region_ids: {value}")
                return None

        return None

    @staticmethod
    def _safe_int(value: str | int | None) -> Optional[int]:
        """Safely convert value to int or return None"""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_bool(value: str | bool | None) -> bool:
        """Safely convert value to bool"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)

    async def process_batch(
        self, raw_messages: list[dict]
    ) -> tuple[list[CameraEventRaw], list[CameraDetectionRaw]]:
        """
        Process a batch of raw messages from Redis stream

        Args:
            raw_messages: List of messages from Redis stream,
                         each message is dict with 'id', 'stream', and 'data' keys

        Returns:
            tuple: (list of CameraEventRaw, list of CameraDetectionRaw)

        Note:
            Validation errors are logged but don't stop processing.
            Invalid messages are skipped and won't appear in results.
        """
        events: list[CameraEventRaw] = []
        detections: list[CameraDetectionRaw] = []

        for message in raw_messages:
            message_id = message.get("id", "unknown")
            data = message.get("data", {})

            if not data:
                logger.warning(f"Empty data in message {message_id}, skipping")
                continue

            # Process event data (always present)
            try:
                event_data = {
                    "camera_id": self._safe_int(data.get("camera_id")),
                    "event_time": self._parse_datetime(data.get("event_time")),
                    "frame_number": self._safe_int(data.get("frame_number")),
                    "has_detection": self._safe_bool(data.get("has_detection", False)),
                    "detection_count": self._safe_int(data.get("detection_count")) or 0,
                    "processing_time_ms": self._safe_int(data.get("processing_time_ms")),
                    "stream_lag_ms": self._safe_int(data.get("stream_lag_ms")),
                }

                # Validate and create event model
                event = CameraEventRaw(**event_data)
                events.append(event)

            except ValidationError as e:
                logger.error(
                    f"Validation error for event in message {message_id}: {e}",
                    extra={"data": data, "errors": e.errors()},
                )
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error processing event in message {message_id}: {e}",
                    extra={"data": data},
                )
                continue

            # Process detection data (only if has_detection is True)
            has_detection = self._safe_bool(data.get("has_detection", False))
            if has_detection:
                try:
                    detection_data = {
                        "event_time": self._parse_datetime(data.get("event_time")),
                        "camera_id": self._safe_int(data.get("camera_id")),
                        "class_id": self._safe_int(data.get("class_id")),
                        "confidence": self._safe_int(data.get("confidence")),
                        "photo_url": data.get("photo_url"),
                        "coord_x": self._safe_int(data.get("coord_x")),
                        "coord_y": self._safe_int(data.get("coord_y")),
                        "region_ids": self._parse_region_ids(data.get("region_ids")),
                        "bbox_width": self._safe_int(data.get("bbox_width")),
                        "bbox_height": self._safe_int(data.get("bbox_height")),
                        "object_id": data.get("object_id"),
                        "track_id": self._safe_int(data.get("track_id")),
                    }

                    # Validate and create detection model
                    detection = CameraDetectionRaw(**detection_data)
                    detections.append(detection)

                except ValidationError as e:
                    logger.error(
                        f"Validation error for detection in message {message_id}: {e}",
                        extra={"data": data, "errors": e.errors()},
                    )
                    # Continue processing other messages
                except Exception as e:
                    logger.error(
                        f"Unexpected error processing detection in message {message_id}: {e}",
                        extra={"data": data},
                    )
                    # Continue processing other messages

        logger.info(
            f"Processed {len(raw_messages)} messages: "
            f"{len(events)} events, {len(detections)} detections"
        )

        return events, detections


# Singleton instance
batch_processor = BatchProcessor()
