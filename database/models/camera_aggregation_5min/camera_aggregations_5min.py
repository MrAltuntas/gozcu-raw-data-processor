"""5-minute camera aggregations table model."""

from sqlalchemy import Column, Integer, BigInteger, SmallInteger, Float, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from database.base import Base


class FiveMinCameraAggregation(Base):
    """5-minute camera aggregation database model.

    Stores aggregated camera detection statistics in 5-minute time buckets.
    Provides pre-computed metrics for faster analytics queries.

    The detection_rate is automatically computed from frames_with_detection
    and total_frames to ensure consistency.
    """

    __tablename__ = "camera_aggregations_5min"

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Core fields
    camera_id = Column(Integer, nullable=False)
    time_bucket = Column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    total_frames = Column(SmallInteger, nullable=False)
    frames_with_detection = Column(SmallInteger, nullable=False)
    detection_rate = Column(
        Float,
        nullable=False
    )

    # Audit fields
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('NOW()')
    )

    # Relationships
    class_stats = relationship(
        "FiveMinCameraAggregationClassStats",
        back_populates="aggregation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    region_stats = relationship(
        "FiveMinCameraAggregationRegionStats",
        back_populates="aggregation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    region_class_stats = relationship(
        "FiveMinCameraAggregationRegionClassStats",
        back_populates="aggregation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Indexes and constraints
    __table_args__ = (
        # Unique constraint on camera_id and time_bucket
        Index(
            'idx_camera_time_unique',
            'camera_id',
            'time_bucket',
            unique=True
        ),
        # Time-based queries
        Index(
            'idx_time_bucket_desc',
            text('time_bucket DESC')
        ),
        # Camera-based time queries
        Index(
            'idx_camera_time_desc',
            'camera_id',
            text('time_bucket DESC')
        ),
        # High activity queries
        Index(
            'idx_detection_rate_desc',
            text('detection_rate DESC')
        ),
        # Audit/log queries
        Index(
            'idx_created_at_desc',
            text('created_at DESC')
        ),
        # Check constraints
        CheckConstraint(
            'detection_rate >= 0 AND detection_rate <= 100',
            name='chk_detection_rate_range'
        ),
        CheckConstraint(
            'frames_with_detection <= total_frames',
            name='chk_frames_with_detection_valid'
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FiveMinCameraAggregation(id={self.id}, "
            f"camera_id={self.camera_id}, "
            f"time_bucket={self.time_bucket}, "
            f"detection_rate={self.detection_rate:.2f}%)>"
        )