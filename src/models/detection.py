"""Detection data model for raw data processing."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CameraDetectionRaw(BaseModel):
    """Raw camera detection data model from Redis stream.

    Represents a single object detection from a camera, including
    bounding box coordinates, classification, and tracking information.
    """

    event_time: datetime = Field(..., description="Timestamp when the detection occurred")
    camera_id: int = Field(..., gt=0, description="Camera identifier, must be positive")
    class_id: int = Field(..., gt=0, description="Detected object class ID, must be positive")
    confidence: int = Field(..., ge=0, le=100, description="Detection confidence score (0-100)")
    photo_url: Optional[str] = Field(None, description="URL to the detection photo/snapshot")
    coord_x: Optional[int] = Field(None, ge=0, description="X coordinate of detection center")
    coord_y: Optional[int] = Field(None, ge=0, description="Y coordinate of detection center")
    region_ids: Optional[list[int]] = Field(None, description="List of region IDs where detection occurred")
    bbox_width: Optional[int] = Field(None, gt=0, description="Bounding box width in pixels")
    bbox_height: Optional[int] = Field(None, gt=0, description="Bounding box height in pixels")
    object_id: Optional[str] = Field(None, description="UUID string identifying the detected object")
    track_id: Optional[int] = Field(None, gt=0, description="Tracking ID for multi-frame object tracking")

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, v: datetime) -> datetime:
        """Ensure event_time is not in the far future."""
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v > now:
            raise ValueError("event_time cannot be in the future")
        return v

    @field_validator("photo_url")
    @classmethod
    def validate_photo_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate photo_url format if provided."""
        if v is not None and v.strip():
            # Basic URL validation
            if not (v.startswith("http://") or v.startswith("https://") or v.startswith("s3://")):
                raise ValueError("photo_url must start with http://, https://, or s3://")
        return v

    @field_validator("object_id")
    @classmethod
    def validate_object_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate object_id is a valid UUID string."""
        if v is not None and v.strip():
            try:
                # Attempt to parse as UUID to validate format
                UUID(v)
            except ValueError:
                raise ValueError("object_id must be a valid UUID string")
        return v

    @field_validator("region_ids")
    @classmethod
    def validate_region_ids(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Validate region_ids contains only positive integers."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("region_ids cannot be an empty list, use None instead")
            for region_id in v:
                if region_id <= 0:
                    raise ValueError("All region_ids must be positive integers")
        return v

    @field_validator("bbox_width", "bbox_height")
    @classmethod
    def validate_bbox_dimensions(cls, v: Optional[int], info) -> Optional[int]:
        """Validate bounding box dimensions are reasonable."""
        if v is not None and v > 10000:
            raise ValueError(f"{info.field_name} exceeds maximum reasonable value of 10000 pixels")
        return v

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "event_time": "2025-11-06T10:30:00",
                "camera_id": 1,
                "class_id": 5,
                "confidence": 95,
                "photo_url": "https://example.com/detections/photo123.jpg",
                "coord_x": 320,
                "coord_y": 240,
                "region_ids": [1, 3],
                "bbox_width": 150,
                "bbox_height": 200,
                "object_id": "550e8400-e29b-41d4-a716-446655440000",
                "track_id": 42
            }
        }
