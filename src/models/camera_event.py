"""Camera event models for raw data processing."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CameraEventRaw(BaseModel):
    """Raw camera event data model from Redis stream.

    Represents a single event from a camera, including metadata about
    detections, processing time, and stream performance.
    """

    camera_id: int = Field(..., gt=0, description="Camera identifier, must be positive")
    event_time: datetime = Field(..., description="Timestamp when the event occurred")
    frame_number: Optional[int] = Field(None, ge=0, description="Frame number in the video stream")
    has_detection: bool = Field(False, description="Whether any detection was found in this frame")
    detection_count: int = Field(0, ge=0, description="Number of detections in this frame")
    processing_time_ms: Optional[int] = Field(None, gt=0, description="Processing time in milliseconds")
    stream_lag_ms: Optional[int] = Field(None, ge=0, description="Stream lag in milliseconds")

    @field_validator("detection_count")
    @classmethod
    def validate_detection_count_with_flag(cls, v: int, info) -> int:
        """Ensure detection_count is consistent with has_detection flag."""
        # Note: info.data contains already validated fields
        if "has_detection" in info.data:
            has_detection = info.data["has_detection"]
            if has_detection and v == 0:
                raise ValueError("detection_count must be > 0 when has_detection is True")
            if not has_detection and v > 0:
                raise ValueError("detection_count must be 0 when has_detection is False")
        return v

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, v: datetime) -> datetime:
        """Ensure event_time is not in the far future."""
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v > now:
            raise ValueError("event_time cannot be in the future")
        return v

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "camera_id": 1,
                "event_time": "2025-11-06T10:30:00",
                "frame_number": 12345,
                "has_detection": True,
                "detection_count": 3,
                "processing_time_ms": 150,
                "stream_lag_ms": 50
            }
        }
