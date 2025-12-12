"""5-minute camera aggregation region-class statistics table model."""

from sqlalchemy import Column, BigInteger, SmallInteger, Float, Index, ForeignKey, ForeignKeyConstraint, text
from sqlalchemy.orm import relationship
from database.base import Base


class FiveMinCameraAggregationRegionClassStats(Base):
    """Region-class relationship statistics for 5-minute camera aggregations.

    Stores detailed detection statistics for each class within specific regions
    during aggregation periods. Enables cross-dimensional analysis of spatial
    and object-type patterns.

    Each record represents statistics for a specific class within a specific region
    during a 5-minute aggregation window.
    """

    __tablename__ = "camera_aggregation_region_class_stats_5min"

    # Composite primary key (three-way relationship)
    aggregation_id = Column(
        BigInteger,
        ForeignKey('camera_aggregations_5min.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    region_id = Column(SmallInteger, primary_key=True, nullable=False)
    class_id = Column(SmallInteger, primary_key=True, nullable=False)

    # Detection statistics
    max_in_frame = Column(SmallInteger, nullable=False)
    min_in_frame = Column(SmallInteger, nullable=False, server_default=text('0'))
    avg_per_frame = Column(Float, nullable=False)
    frames_present = Column(SmallInteger, nullable=False)

    # Relationships
    aggregation = relationship(
        "FiveMinCameraAggregation",
        back_populates="region_class_stats"
    )
    region_stat = relationship(
        "FiveMinCameraAggregationRegionStats",
        foreign_keys="[FiveMinCameraAggregationRegionClassStats.aggregation_id, FiveMinCameraAggregationRegionClassStats.region_id]",
        back_populates="region_class_stats"
    )
    class_stat = relationship(
        "FiveMinCameraAggregationClassStats",
        foreign_keys="[FiveMinCameraAggregationRegionClassStats.aggregation_id, FiveMinCameraAggregationRegionClassStats.class_id]",
        back_populates="region_class_stats"
    )

    # Indexes and constraints
    __table_args__ = (
        # Composite foreign key constraints
        ForeignKeyConstraint(
            ['aggregation_id', 'region_id'],
            ['camera_aggregation_region_stats_5min.aggregation_id', 'camera_aggregation_region_stats_5min.region_id'],
            ondelete='CASCADE'
        ),
        ForeignKeyConstraint(
            ['aggregation_id', 'class_id'],
            ['camera_aggregation_class_stats_5min.aggregation_id', 'camera_aggregation_class_stats_5min.class_id'],
            ondelete='CASCADE'
        ),
        # Region-class queries (start with region, filter by class)
        Index(
            'idx_region_class_aggregation',
            'region_id',
            'class_id',
            'aggregation_id'
        ),
        # Class-region queries (start with class, filter by region)
        Index(
            'idx_class_region_aggregation',
            'class_id',
            'region_id',
            'aggregation_id'
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FiveMinCameraAggregationRegionClassStats("
            f"aggregation_id={self.aggregation_id}, "
            f"region_id={self.region_id}, "
            f"class_id={self.class_id}, "
            f"max_in_frame={self.max_in_frame})>"
        )
