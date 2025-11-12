"""Batch processing service"""
import json
import logging
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from database.models.camera_events_raw import CameraEventRaw

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
    ) -> list[CameraEventRaw]:
        """
        Process a batch of raw messages from Redis stream

        Args:
            raw_messages: List of messages from Redis stream,
                         each message is dict with 'id', 'stream', and 'data' keys

        Returns:
            list: list of CameraEventRaw with JSONB event data

        Note:
            Validation errors are logged but don't stop processing.
            Invalid messages are skipped and won't appear in results.
        """
        events: list[CameraEventRaw] = []

        for message in raw_messages:
            message_id = message.get("id", "unknown")
            data = message.get("data", {})

            if not data:
                logger.warning(f"Empty data in message {message_id}, skipping")
                continue

            try:
                # Extract and validate required fields first
                camera_id = self._safe_int(data.get("cameraID") or data.get("camera_id"))
                event_time = self._parse_datetime(data.get("eventDate") or data.get("event_time"))
                
                if not camera_id or not event_time:
                    logger.warning(f"Missing required fields in message {message_id}: camera_id={camera_id}, event_time={event_time}")
                    continue

                # Build detected objects array for JSONB
                detected_objects = []
                
                # Check if we have detection data
                detections_data = data.get("detectedObjects")
                logger.info(f"Message {message_id}: Raw detections_data = {detections_data} (type: {type(detections_data)})")
                
                # Parse JSON string if needed
                if isinstance(detections_data, str):
                    try:
                        detections_data = json.loads(detections_data)
                        logger.info(f"Message {message_id}: Parsed detections_data = {detections_data}")
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse detectedObjects JSON in message {message_id}")
                        detections_data = []
                
                if detections_data is not None and isinstance(detections_data, list):
                    # Multiple detections format (new format)
                    logger.info(f"Message {message_id}: Processing {len(detections_data)} detections")
                    for i, detection in enumerate(detections_data):
                        logger.info(f"Message {message_id}: Processing detection {i}: {detection}")
                        detection_obj = self._build_detection_object(detection)
                        logger.info(f"Message {message_id}: Built detection object {i}: {detection_obj}")
                        if detection_obj:
                            detected_objects.append(detection_obj)
                else:
                    # Single detection or legacy format
                    if self._safe_bool(data.get("has_detection", False)):
                        detection_obj = self._build_detection_object(data)
                        if detection_obj:
                            detected_objects.append(detection_obj)

                # Create JSONB event data structure matching expected format
                logger.info(f"Message {message_id}: Final detected_objects count: {len(detected_objects)}")
                event_data_json = {
                    "detectedObjects": detected_objects
                }
                
                # Add optional metadata if present
                optional_fields = {
                    "frame_number": self._safe_int(data.get("frame_number")),
                    "processing_time_ms": self._safe_int(data.get("processing_time_ms")),
                    "stream_lag_ms": self._safe_int(data.get("stream_lag_ms"))
                }
                
                # Add non-None optional fields
                for field, value in optional_fields.items():
                    if value is not None:
                        event_data_json[field] = value

                # Create SQLAlchemy model instance
                event = CameraEventRaw(
                    camera_id=camera_id,
                    event_time=event_time,
                    event_data=event_data_json
                )
                events.append(event)

            except Exception as e:
                logger.error(
                    f"Error processing message {message_id}: {e}",
                    extra={"data": data},
                )
                continue

        logger.info(
            f"Processed {len(raw_messages)} messages: "
            f"{len(events)} events with JSONB data"
        )

        return events

    def _build_detection_object(self, data: dict) -> Optional[dict]:
        """
        Build a detection object from raw data that matches Pydantic model structure
        
        Args:
            data: Raw detection data dictionary
            
        Returns:
            dict: Detection object matching expected format or None if invalid
        """
        try:
            detection_obj = {}
            
            # Map fields according to Pydantic model (CameraEventCreate.DetectedObject)
            field_mappings = {
                "className": ["className", "class_name", "class_id"],
                "confidence": ["confidence"],
                "photoUrl": ["photoUrl", "photo_url"],
                "coordinateX": ["coordinateX", "coordinate_x", "coord_x"],
                "coordinateY": ["coordinateY", "coordinate_y", "coord_y"],
                "regionID": ["regionID", "region_id", "region_ids"]
            }
            
            for target_field, source_fields in field_mappings.items():
                for source_field in source_fields:
                    if source_field in data and data[source_field] is not None:
                        if target_field == "className":
                            detection_obj[target_field] = self._safe_int(data[source_field])
                        elif target_field == "confidence":
                            confidence = self._safe_int(data[source_field])
                            if confidence is not None and 0 <= confidence <= 100:
                                detection_obj[target_field] = confidence
                        elif target_field in ["coordinateX", "coordinateY"]:
                            detection_obj[target_field] = self._safe_int(data[source_field])
                        elif target_field == "photoUrl":
                            detection_obj[target_field] = str(data[source_field])
                        elif target_field == "regionID":
                            region_ids = self._parse_region_ids(data[source_field])
                            if region_ids is not None:
                                detection_obj[target_field] = region_ids
                        break
            
            # Validate minimum required fields are present (matching Pydantic model requirements)
            required_fields = ["className", "confidence", "photoUrl", "coordinateX", "coordinateY"]
            if all(field in detection_obj for field in required_fields):
                return detection_obj
            else:
                logger.debug(f"Detection missing required fields {required_fields}. Has: {list(detection_obj.keys())}")
                return None
                
        except Exception as e:
            logger.warning(f"Error building detection object: {e}")
            return None


# Singleton instance
batch_processor = BatchProcessor()
