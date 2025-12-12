"""
Test module for FiveMinuteAggregateJob.

This test validates the complete lifecycle of the five minute aggregate job:
- Job execution with real/synthetic data
- Database connection cleanup
- Resource management
- Log output verification

Usage:
    python -m src.tests.jobs.test_five_minute_aggregate
    python -m src.tests.jobs.test_five_minute_aggregate --data-source synthetic
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from src.jobs import FiveMinuteAggregateJob, JobConfig
from src.core.database import db_manager


class TestFiveMinuteAggregate:
    """
    Test suite for FiveMinuteAggregateJob.

    Supports two data source modes:
    - 'db': Uses existing data from camera_events_raw table
    - 'synthetic': Inserts test data, runs job, then cleans up
    """

    def __init__(self, data_source: str = 'db'):
        """
        Initialize test suite.

        Args:
            data_source: 'db' for existing data, 'synthetic' for test data
        """
        self.data_source = data_source
        self.logger = logging.getLogger(__name__)
        self.job: Optional[FiveMinuteAggregateJob] = None
        self.synthetic_event_ids: List[int] = []

    async def setup(self) -> None:
        """Setup test environment and optionally insert synthetic data."""
        self.logger.info("="*60)
        self.logger.info(f"SETUP: Test with data_source='{self.data_source}'")
        self.logger.info("="*60)

        if self.data_source == 'synthetic':
            await self._insert_synthetic_data()
        else:
            self.logger.info("Using existing database data (no synthetic data)")

    async def _insert_synthetic_data(self) -> None:
        """Insert test data into camera_events_raw table."""
        self.logger.info("Inserting synthetic test data...")

        # Connect to database
        await db_manager.connect()

        # Generate test events (last 3 minutes to ensure they're captured)
        now = datetime.now()
        test_events = [
            {
                'camera_id': 1,
                'event_time': now - timedelta(minutes=2, seconds=30),
                'has_detection': True,
                'detection_count': 2,
                'detected_objects': [
                    {
                        "className": 0,
                        "confidence": 85,
                        "photoUrl": "test_images/person_85.jpg",
                        "coordinateX": 450,
                        "coordinateY": 320,
                        "regionID": [1, 3]
                    },
                    {
                        "className": 2,
                        "confidence": 92,
                        "photoUrl": "test_images/car_92.jpg",
                        "coordinateX": 120,
                        "coordinateY": 580,
                        "regionID": [2]
                    }
                ]
            },
            {
                'camera_id': 1,
                'event_time': now - timedelta(minutes=1, seconds=45),
                'has_detection': True,
                'detection_count': 1,
                'detected_objects': [
                    {
                        "className": 0,
                        "confidence": 88,
                        "photoUrl": "test_images/person_88.jpg",
                        "coordinateX": 500,
                        "coordinateY": 430,
                        "regionID": []
                    }
                ]
            },
            {
                'camera_id': 1,
                'event_time': now - timedelta(minutes=1),
                'has_detection': False,
                'detection_count': 0,
                'detected_objects': []
            }
        ]

        try:
            async with db_manager.get_connection() as conn:
                for event in test_events:
                    query = """
                    INSERT INTO camera_events_raw
                        (camera_id, event_time, has_detection, detection_count, detected_objects)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """
                    result = await conn.fetchrow(
                        query,
                        event['camera_id'],
                        event['event_time'],
                        event['has_detection'],
                        event['detection_count'],
                        event['detected_objects']
                    )
                    self.synthetic_event_ids.append(result['id'])

            self.logger.info(f"Inserted {len(test_events)} synthetic events (IDs: {self.synthetic_event_ids})")

        except Exception as e:
            self.logger.error(f"Failed to insert synthetic data: {e}", exc_info=True)
            raise
        finally:
            await db_manager.disconnect()

    async def test_job_execution(self) -> bool:
        """
        Test main job execution.

        Returns:
            bool: True if job executed successfully
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST: Job Execution")
        self.logger.info("="*60)

        try:
            # Create job with config
            config = JobConfig(camera_ids=[1])
            self.job = FiveMinuteAggregateJob(config)

            # Run the job
            self.logger.info("Starting FiveMinuteAggregateJob...")
            start_time = datetime.now()

            await self.job.run()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.info(f"✓ Job completed successfully in {duration:.2f} seconds")
            return True

        except Exception as e:
            self.logger.error(f"✗ Job execution failed: {e}", exc_info=True)
            return False

    async def test_database_cleanup(self) -> bool:
        """
        Test that database connections are properly closed.

        Returns:
            bool: True if database is properly cleaned up
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST: Database Cleanup")
        self.logger.info("="*60)

        try:
            is_connected = db_manager.is_connected

            if not is_connected:
                self.logger.info("✓ Database connection is properly closed")
                return True
            else:
                self.logger.error("✗ Database connection is still open!")
                return False

        except Exception as e:
            self.logger.error(f"✗ Database cleanup test failed: {e}", exc_info=True)
            return False

    async def test_logs(self) -> bool:
        """
        Test that appropriate logs were generated.

        Returns:
            bool: True if logs are as expected
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST: Log Verification")
        self.logger.info("="*60)

        # This is a simple check - in production you'd capture logs
        # For now, we just verify job object state
        try:
            if self.job:
                if self.job.start_time and self.job.end_time:
                    duration = (self.job.end_time - self.job.start_time).total_seconds()
                    self.logger.info(f"✓ Job timing recorded: {duration:.2f} seconds")
                    return True
                else:
                    self.logger.error("✗ Job timing not recorded")
                    return False
            else:
                self.logger.error("✗ Job object not created")
                return False

        except Exception as e:
            self.logger.error(f"✗ Log verification failed: {e}", exc_info=True)
            return False

    async def cleanup(self) -> None:
        """Cleanup test environment and remove synthetic data if used."""
        self.logger.info("\n" + "="*60)
        self.logger.info("CLEANUP")
        self.logger.info("="*60)

        if self.data_source == 'synthetic' and self.synthetic_event_ids:
            await self._remove_synthetic_data()
        else:
            self.logger.info("No cleanup needed (using existing DB data)")

    async def _remove_synthetic_data(self) -> None:
        """Remove synthetic test data from database."""
        if not self.synthetic_event_ids:
            return

        self.logger.info(f"Removing {len(self.synthetic_event_ids)} synthetic events...")

        try:
            await db_manager.connect()

            async with db_manager.get_connection() as conn:
                query = """
                DELETE FROM camera_events_raw
                WHERE id = ANY($1)
                """
                await conn.execute(query, self.synthetic_event_ids)

            self.logger.info(f"✓ Removed synthetic events (IDs: {self.synthetic_event_ids})")

        except Exception as e:
            self.logger.error(f"Failed to remove synthetic data: {e}", exc_info=True)
        finally:
            await db_manager.disconnect()

    async def run_all_tests(self) -> None:
        """Run complete test suite."""
        results = {
            'setup': False,
            'job_execution': False,
            'database_cleanup': False,
            'logs': False,
            'cleanup': False
        }

        try:
            # Setup
            await self.setup()
            results['setup'] = True

            # Run tests
            results['job_execution'] = await self.test_job_execution()
            results['database_cleanup'] = await self.test_database_cleanup()
            results['logs'] = await self.test_logs()

        except Exception as e:
            self.logger.error(f"Test suite failed: {e}", exc_info=True)
        finally:
            # Always cleanup
            await self.cleanup()
            results['cleanup'] = True

        # Print summary
        self._print_summary(results)

    def _print_summary(self, results: dict) -> None:
        """Print test results summary."""
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("="*60)

        total = len(results)
        passed = sum(1 for r in results.values() if r)

        for test_name, passed_flag in results.items():
            status = "✓ PASS" if passed_flag else "✗ FAIL"
            self.logger.info(f"{status}: {test_name}")

        self.logger.info("-"*60)
        self.logger.info(f"Total: {passed}/{total} tests passed")
        self.logger.info("="*60)


async def main():
    """Main entry point for running tests."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Parse data source from command line
    data_source = 'db'  # default
    if len(sys.argv) > 1 and sys.argv[1] == '--data-source' and len(sys.argv) > 2:
        data_source = sys.argv[2]

    if data_source not in ['db', 'synthetic']:
        logger.error(f"Invalid data_source: {data_source}. Use 'db' or 'synthetic'")
        sys.exit(1)

    logger.info(f"Starting test suite with data_source='{data_source}'")

    # Run tests
    test_suite = TestFiveMinuteAggregate(data_source=data_source)
    await test_suite.run_all_tests()


if __name__ == "__main__":
    """Entry point when running as a script."""
    asyncio.run(main())
