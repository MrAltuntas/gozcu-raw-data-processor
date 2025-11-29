"""
5-minute camera event aggregation job.

This job processes camera events from the last 5 minutes and generates
detailed summaries including detection analysis, gap detection, and statistics.

Usage:
    python -m src.jobs.five_minute_aggregate
    python -m src.jobs.five_minute_aggregate --camera-id 1
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.jobs.base_job import BaseJob
from src.jobs.models import CameraSummary, DetectedClassInfo, GapInfo, JobConfig
from src.core.database import db_manager


class FiveMinuteAggregateJob(BaseJob):
    """
    Job that aggregates camera events into 5-minute summaries.
    
    This job:
    1. Queries camera_events_raw for the last 5 minutes
    2. Processes detection data by class
    3. Calculates statistics (rates, confidence, gaps)
    4. Generates detailed JSON output
    """
    
    def __init__(self, config: Optional[JobConfig] = None):
        """Initialize the aggregation job."""
        super().__init__("five_minute_aggregate")
        self.config = config or JobConfig()
    
    async def execute(self) -> None:
        """Main job execution logic - simplified test version."""
        self.logger.info("Starting simple test job")
        
        try:
            # Test: Just query one row from camera_events_raw
            result = await self._test_db_query()
            
            if result:
                self.logger.info(f"SUCCESS: Found camera event - Camera ID: {result.get('camera_id')}, "
                               f"Event time: {result.get('event_time')}")
            else:
                self.logger.info("No data found in camera_events_raw table")
                
        except Exception as e:
            self.logger.error(f"Job execution failed: {e}", exc_info=True)
            raise
    
    async def _calculate_time_window(self) -> tuple[datetime, datetime]:
        """Calculate the time window for processing."""
        # TODO: Implement time window calculation
        end_time = datetime.now() - timedelta(seconds=30)  # 30s buffer
        start_time = end_time - timedelta(minutes=self.config.period_minutes)
        return start_time, end_time
    
    async def _get_camera_ids(self) -> List[int]:
        """Get list of camera IDs to process."""
        # TODO: Implement camera ID discovery
        if self.config.camera_ids:
            return self.config.camera_ids
        
        # If no specific cameras, get all active cameras from DB
        return [1]  # Placeholder
    
    async def _process_camera(self, camera_id: int, time_window: tuple[datetime, datetime]) -> CameraSummary:
        """Process events for a single camera."""
        # TODO: Implement camera processing logic
        start_time, end_time = time_window
        
        self.logger.info(f"Processing camera {camera_id} from {start_time} to {end_time}")
        
        # 1. Query raw events
        events = await self._query_camera_events(camera_id, start_time, end_time)
        
        # 2. Process by detected classes
        detected_classes = await self._analyze_detected_classes(events)
        
        # 3. Create summary
        summary = CameraSummary(
            camera_id=camera_id,
            period_start=start_time,
            period_end=end_time,
            total_events=len(events),
            detected_classes=detected_classes
        )
        
        return summary
    
    async def _test_db_query(self) -> Optional[dict]:
        """Simple test query - get one row from camera_events_raw."""
        try:
            query = """
            SELECT camera_id, event_time, has_detection, detection_count
            FROM camera_events_raw 
            ORDER BY event_time DESC 
            LIMIT 1
            """
            
            async with db_manager.get_connection() as conn:
                result = await conn.fetch(query)
                
                if result:
                    row = result[0]
                    return {
                        'camera_id': row['camera_id'],
                        'event_time': row['event_time'], 
                        'has_detection': row['has_detection'],
                        'detection_count': row['detection_count']
                    }
                return None
            
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return None
    
    async def _analyze_detected_classes(self, events: List[dict]) -> Dict[str, DetectedClassInfo]:
        """Analyze events and group by detected object classes."""
        # TODO: Implement class analysis logic
        # This is where the complex detection analysis happens
        return {}  # Placeholder
    
    async def _output_summary(self, summary: CameraSummary) -> None:
        """Output the summary (log, save to DB, send to external system, etc.)."""
        # TODO: Implement output logic
        self.logger.info(f"Camera {summary.camera_id} summary: {summary.total_events} events, "
                        f"{len(summary.detected_classes)} object classes detected")


async def main():
    """Main entry point - runs every 10 seconds for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting test job - will run every 10 seconds")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            try:
                logger.info("="*50)
                logger.info("Running job iteration")
                
                config = JobConfig()
                job = FiveMinuteAggregateJob(config)
                
                await job.run()
                
                logger.info("Job iteration completed, waiting 10 seconds...")
                
            except Exception as e:
                logger.error(f"Job iteration failed: {e}", exc_info=True)
            
            # Wait 10 seconds before next run
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Job stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    """Entry point when running as a script."""
    asyncio.run(main())