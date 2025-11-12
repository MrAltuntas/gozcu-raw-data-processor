"""Camera events raw table model."""

from sqlalchemy import Column, Integer, Boolean, SmallInteger, Computed, Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from database.base import Base


class CameraEventRaw(Base):
    """Camera event raw database model.
    
    Stores complete event data in JSONB format with optimized computed columns
    for query performance. Uses TimescaleDB hypertable for time-series optimization.
    
    Note: Hypertable creation, retention policies, and statistics configuration
    must be handled in migration scripts, not in the SQLAlchemy model.
    """
    
    __tablename__ = "camera_events_raw"
    
    # Core fields
    camera_id = Column(Integer, nullable=False, primary_key=True)
    event_time = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        primary_key=True
    )
    event_data = Column(JSONB, nullable=False)
    
    # Computed columns (GENERATED ALWAYS AS STORED)
    has_detection = Column(
        Boolean,
        Computed(
            "COALESCE(jsonb_array_length(event_data->'detectedObjects'), 0) > 0",
            persisted=True
        )
    )
    detection_count = Column(
        SmallInteger,
        Computed(
            "COALESCE(jsonb_array_length(event_data->'detectedObjects'), 0)",
            persisted=True
        )
    )
    
    # Partial index for queries filtering by detection
    __table_args__ = (
        Index(
            'idx_camera_events_detection',
            'camera_id',
            text('event_time DESC'),  # DESC için text() kullan
            postgresql_where=text('has_detection = true')  # WHERE clause için text()
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<CameraEventRaw(camera_id={self.camera_id}, "
            f"event_time={self.event_time}, "
            f"has_detection={self.has_detection})>"
        )