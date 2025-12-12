"""5-minute camera aggregation region statistics table model."""

from sqlalchemy import Column, BigInteger, SmallInteger, Integer, Float, String, Index, CheckConstraint, ForeignKey, text
from sqlalchemy.orm import relationship
from database.base import Base


class FiveMinCameraAggregationRegionStats(Base):
    """Region-level statistics for 5-minute camera aggregations.

    Stores detection statistics and activity patterns per region for each aggregation period.
    Provides spatial analysis capabilities by tracking activity types in different regions.

    Each record represents statistics for a specific region within a 5-minute aggregation window.
    """

    __tablename__ = "camera_aggregation_region_stats_5min"

    # Composite primary key
    aggregation_id = Column(
        BigInteger,
        ForeignKey('camera_aggregations_5min.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    region_id = Column(SmallInteger, primary_key=True, nullable=False)

    # Detection and activity statistics
    total_detections = Column(Integer, nullable=False)
    avg_confidence = Column(Float, nullable=False)
    activity_type = Column(
        String(20),
        nullable=False
    )

    # Relationships
    aggregation = relationship(
        "FiveMinCameraAggregation",
        back_populates="region_stats"
    )
    region_class_stats = relationship(
        "FiveMinCameraAggregationRegionClassStats",
        foreign_keys="[FiveMinCameraAggregationRegionClassStats.aggregation_id, FiveMinCameraAggregationRegionClassStats.region_id]",
        back_populates="region_stat",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Indexes and constraints
    __table_args__ = (
        # Region-based queries
        Index(
            'idx_region_aggregation',
            'region_id',
            'aggregation_id'
        ),
        # Activity type filtering
        Index(
            'idx_activity_type',
            'activity_type'
        ),
        # Composite analysis queries
        Index(
            'idx_region_activity_detections',
            'region_id',
            'activity_type',
            text('total_detections DESC')
        ),
        # Check constraints
        CheckConstraint(
            "activity_type IN ('high_traffic', 'low_traffic', 'stationary', 'transient')",
            name='chk_activity_type_valid'
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FiveMinCameraAggregationRegionStats("
            f"aggregation_id={self.aggregation_id}, "
            f"region_id={self.region_id}, "
            f"activity_type='{self.activity_type}', "
            f"total_detections={self.total_detections})>"
        )
