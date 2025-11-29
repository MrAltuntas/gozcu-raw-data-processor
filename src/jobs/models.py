"""Data models for job outputs and configurations."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GapInfo(BaseModel):
    """Information about detection gaps in a time period."""
    longest_gap_samples: int = Field(..., description="Longest gap in number of samples")
    gap_count: int = Field(..., description="Total number of gaps found")


class RegionDistribution(BaseModel):
    """Distribution of detections across regions."""
    # TODO: Define region distribution model
    pass


class DetectedClassInfo(BaseModel):
    """
    Detailed information about a specific detected class in a time period.
    
    This model represents the complex JSON structure for each detected object class.
    """
    class_id: int = Field(..., description="Object class ID")
    first_seen: str = Field(..., description="Time of first detection (HH:MM:SS)")
    last_seen: str = Field(..., description="Time of last detection (HH:MM:SS)")
    detection_count: int = Field(..., description="Total number of detections")
    detection_rate: float = Field(..., ge=0, le=1, description="Detection rate (count/total_possible)")
    avg_confidence: float = Field(..., ge=0, le=100, description="Average confidence score")
    is_consistent: bool = Field(..., description="Whether detection is consistent (no large gaps)")
    gap_info: GapInfo = Field(..., description="Information about detection gaps")
    region_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution across regions")
    photo_samples: List[str] = Field(default_factory=list, max_items=3, description="Sample photo URLs")


class CameraSummary(BaseModel):
    """
    Complete 5-minute summary for a single camera.
    
    This matches the target JSON structure requested.
    """
    camera_id: int = Field(..., description="Camera ID")
    period: str = Field(default="5min", description="Time period of summary")
    detected_classes: Dict[str, DetectedClassInfo] = Field(
        default_factory=dict, 
        description="Map of class_id -> class information"
    )
    
    # Metadata (optional)
    period_start: Optional[datetime] = Field(None, description="Start of the period")
    period_end: Optional[datetime] = Field(None, description="End of the period")
    total_events: Optional[int] = Field(None, description="Total events in period")


class JobConfig(BaseModel):
    """Configuration for job execution."""
    camera_ids: Optional[List[int]] = Field(None, description="Specific camera IDs to process")
    period_minutes: int = Field(default=5, description="Time period in minutes")
    min_gap_samples: int = Field(default=150, description="Minimum gap samples for inconsistent flag")
    
    # TODO: Add other configuration options as needed