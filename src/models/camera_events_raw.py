"""Camera event model for JSONB table operations."""

from datetime import datetime
from pydantic import BaseModel, Field


class CameraEventCreate(BaseModel):
    """Model for validating incoming camera event payloads."""

    class DetectedObject(BaseModel):
        """Single detected object in the frame."""
        className: int
        confidence: int = Field(..., ge=0, le=100)
        photoUrl: str
        coordinateX: int
        coordinateY: int
        regionID: list[int] = Field(default_factory=list)

    camera_id: int = Field(..., gt=0, alias="cameraID")
    event_time: datetime = Field(..., alias="eventDate")
    detected_objects: list[DetectedObject] = Field(default_factory=list, alias="detectedObjects")

    class Config:
        populate_by_name = True