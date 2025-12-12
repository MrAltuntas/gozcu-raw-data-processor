"""5-minute camera aggregation class statistics table model."""

from sqlalchemy import Column, BigInteger, SmallInteger, Integer, Float, Index, CheckConstraint, ForeignKey, text
from sqlalchemy.orm import relationship
from database.base import Base


class FiveMinCameraAggregationClassStats(Base):
    """Class-level statistics for 5-minute camera aggregations.

    Stores detailed detection statistics per class for each aggregation period.
    This table provides granular insights into object detection patterns by class type.

    Each record represents statistics for a specific class within a 5-minute aggregation window.
    """

    __tablename__ = "camera_aggregation_class_stats_5min"

    # Composite primary key
    aggregation_id = Column(
        BigInteger,
        ForeignKey('camera_aggregations_5min.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    class_id = Column(SmallInteger, primary_key=True, nullable=False)

    # Detection statistics
    total_detections = Column(Integer, nullable=False)
    max_in_frame = Column(SmallInteger, nullable=False)
    min_in_frame = Column(SmallInteger, nullable=False, server_default=text('0'))
    avg_per_frame = Column(Float, nullable=False)
    frames_present = Column(SmallInteger, nullable=False)
    avg_confidence = Column(Float, nullable=False)

    # Relationships
    aggregation = relationship(
        "FiveMinCameraAggregation",
        back_populates="class_stats"
    )
    region_class_stats = relationship(
        "FiveMinCameraAggregationRegionClassStats",
        foreign_keys="[FiveMinCameraAggregationRegionClassStats.aggregation_id, FiveMinCameraAggregationRegionClassStats.class_id]",
        back_populates="class_stat",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Indexes and constraints
    __table_args__ = (
        # Class-based queries
        Index(
            'idx_class_aggregation',
            'class_id',
            'aggregation_id'
        ),
        # Confidence analysis queries
        Index(
            'idx_class_confidence_desc',
            'class_id',
            text('avg_confidence DESC')
        ),
        # Density/volume analysis queries
        Index(
            'idx_class_detections_desc',
            'class_id',
            text('total_detections DESC')
        ),
        # Partial index for high activity scenarios
        Index(
            'idx_high_activity_class',
            'class_id',
            'aggregation_id',
            postgresql_where=text('total_detections > 100')
        ),
        # Check constraints
        CheckConstraint(
            'avg_confidence >= 0 AND avg_confidence <= 100',
            name='chk_avg_confidence_range'
        ),
        CheckConstraint(
            'min_in_frame <= max_in_frame',
            name='chk_min_max_frame_valid'
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FiveMinCameraAggregationClassStats("
            f"aggregation_id={self.aggregation_id}, "
            f"class_id={self.class_id}, "
            f"total_detections={self.total_detections}, "
            f"avg_confidence={self.avg_confidence:.2f})>"
        )
