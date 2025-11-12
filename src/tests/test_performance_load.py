"""Performance load test for Redis to database integration."""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.core.redis_client import redis_manager
from src.core.database import db_manager
from src.repositories.camera_events_raw_repository import camera_events_raw_repository
from src.config.settings import settings

logger = logging.getLogger(__name__)


class PerformanceLoadTest:
    """Performance load test for processing 150 messages per second."""

    def __init__(self, target_rps: int = 10000, test_duration_seconds: int = 1):
        """
        Initialize performance test.
        
        Args:
            target_rps: Target requests per second
            test_duration_seconds: How long to send messages
        """
        self.target_rps = target_rps
        self.test_duration_seconds = test_duration_seconds
        self.total_messages = target_rps * test_duration_seconds
        
    def generate_payload_templates(self) -> List[Dict[str, Any]]:
        """Generate base payload templates based on existing test patterns."""
        templates = [
            # Template 1: Multiple detections (high load)
            {
                "cameraID": None,  # Will be set dynamically
                "eventDate": None,  # Will be set dynamically
                "detectedObjects": [
                    {
                        "className": 0,
                        "confidence": random.randint(80, 95),
                        "photoUrl": f"kapi_saved_images/person_{random.randint(80, 95)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(100, 800),
                        "coordinateY": random.randint(100, 600),
                        "regionID": [1, 3]
                    },
                    {
                        "className": 2,
                        "confidence": random.randint(85, 98),
                        "photoUrl": f"kapi_saved_images/car_{random.randint(85, 98)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(50, 700),
                        "coordinateY": random.randint(200, 700),
                        "regionID": [2]
                    }
                ]
            },
            # Template 2: Single detection
            {
                "cameraID": None,
                "eventDate": None,
                "detectedObjects": [
                    {
                        "className": 3,
                        "confidence": random.randint(75, 95),
                        "photoUrl": f"garage_saved_images/vehicle_{random.randint(75, 95)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(10, 500),
                        "coordinateY": random.randint(50, 400),
                        "regionID": []
                    }
                ]
            },
            # Template 3: No detections
            {
                "cameraID": None,
                "eventDate": None,
                "detectedObjects": []
            },
            # Template 4: Person detection
            {
                "cameraID": None,
                "eventDate": None,
                "detectedObjects": [
                    {
                        "className": 1,
                        "confidence": random.randint(70, 90),
                        "photoUrl": f"entrance_saved_images/person_{random.randint(70, 90)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(200, 600),
                        "coordinateY": random.randint(100, 500),
                        "regionID": [4, 5]
                    }
                ]
            },
            # Template 5: Multi-object scene
            {
                "cameraID": None,
                "eventDate": None,
                "detectedObjects": [
                    {
                        "className": 0,
                        "confidence": random.randint(85, 95),
                        "photoUrl": f"multi_saved_images/person_{random.randint(85, 95)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(300, 700),
                        "coordinateY": random.randint(200, 500),
                        "regionID": [1, 2, 3]
                    },
                    {
                        "className": 2,
                        "confidence": random.randint(88, 97),
                        "photoUrl": f"multi_saved_images/car_{random.randint(88, 97)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(100, 400),
                        "coordinateY": random.randint(300, 600),
                        "regionID": [2, 4]
                    },
                    {
                        "className": 1,
                        "confidence": random.randint(82, 93),
                        "photoUrl": f"multi_saved_images/bike_{random.randint(82, 93)}_{int(time.time())}.jpg",
                        "coordinateX": random.randint(500, 750),
                        "coordinateY": random.randint(150, 400),
                        "regionID": [1]
                    }
                ]
            }
        ]
        return templates

    def generate_test_payloads(self) -> List[Dict[str, Any]]:
        """
        Generate test payloads with unique timestamps.
        
        Returns:
            List of test payloads with unique eventDate and random camera IDs
        """
        templates = self.generate_payload_templates()
        payloads = []
        
        # Start time for generating unique timestamps
        base_time = datetime.now()
        microsecond_increment = 1000000 // self.target_rps  # Distribute across 1 second
        
        for i in range(self.total_messages):
            # Select random template
            template = random.choice(templates)
            payload = json.loads(json.dumps(template))  # Deep copy
            
            # Set unique timestamp (microsecond precision)
            event_time = base_time + timedelta(microseconds=i * microsecond_increment)
            payload["eventDate"] = event_time.isoformat()
            
            # Set random camera ID (1-10)
            payload["cameraID"] = random.randint(1, 10)
            
            # Randomize photo URLs to make them unique
            for detection in payload.get("detectedObjects", []):
                if "photoUrl" in detection:
                    timestamp_suffix = int(time.time() * 1000000) + i
                    detection["photoUrl"] = detection["photoUrl"].replace(
                        f"_{int(time.time())}.jpg",
                        f"_{timestamp_suffix}.jpg"
                    )
            
            payloads.append(payload)
        
        logger.info(f"Generated {len(payloads)} test payloads")
        return payloads

    async def write_to_redis_parallel(self, payloads: List[Dict[str, Any]]) -> List[str]:
        """
        Write payloads to Redis stream in parallel for maximum speed.
        
        Args:
            payloads: List of test payloads
            
        Returns:
            List of message IDs from Redis
        """
        client = redis_manager.get_client()
        
        async def write_single_payload(payload: Dict[str, Any]) -> str:
            """Write a single payload to Redis."""
            # Convert payload to Redis stream format
            redis_payload = {}
            for key, value in payload.items():
                if isinstance(value, (dict, list)):
                    redis_payload[key] = json.dumps(value)
                else:
                    redis_payload[key] = str(value)
            
            # Add to stream
            message_id = await client.xadd(
                name=settings.redis.stream_key,
                fields=redis_payload
            )
            return message_id
        
        # Execute all writes in parallel using asyncio.gather
        start_time = time.perf_counter()
        message_ids = await asyncio.gather(
            *[write_single_payload(payload) for payload in payloads],
            return_exceptions=True
        )
        end_time = time.perf_counter()
        
        # Filter out exceptions and get successful message IDs
        successful_ids = [msg_id for msg_id in message_ids if isinstance(msg_id, str)]
        failed_count = len(message_ids) - len(successful_ids)
        
        write_duration = end_time - start_time
        actual_rps = len(successful_ids) / write_duration if write_duration > 0 else 0
        
        logger.info(
            f"Redis write completed: {len(successful_ids)} successful, {failed_count} failed "
            f"in {write_duration:.3f}s (actual: {actual_rps:.1f} RPS)"
        )
        
        return successful_ids

    async def count_database_records(self, start_time: datetime, end_time: datetime) -> int:
        """
        Count records in database within time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Number of records found
        """
        async with db_manager.get_connection() as conn:
            query = """
                SELECT COUNT(*) 
                FROM camera_events_raw 
                WHERE event_time >= $1 AND event_time <= $2
            """
            result = await conn.fetchrow(query, start_time, end_time)
            return result[0] if result else 0

    async def cleanup_test_data(self, start_time: datetime, end_time: datetime) -> int:
        """
        Clean up test data from database.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Number of records deleted
        """
        async with db_manager.get_connection() as conn:
            query = """
                DELETE FROM camera_events_raw 
                WHERE event_time >= $1 AND event_time <= $2
            """
            result = await conn.execute(query, start_time, end_time)
            # Extract count from result like "DELETE 123"
            if isinstance(result, str) and result.startswith("DELETE "):
                return int(result.split()[1])
            return 0

    async def run_performance_test(self) -> Dict[str, Any]:
        """
        Run the complete performance test.
        
        Returns:
            Test results with metrics
        """
        logger.info(f"Starting performance test: {self.target_rps} RPS for {self.test_duration_seconds}s")
        
        # Initialize connections
        await redis_manager.connect()
        await db_manager.connect()
        
        try:
            # Generate test payloads
            payloads = self.generate_test_payloads()
            test_start_time = datetime.now()
            
            # Phase 1: Write to Redis (measure speed)
            logger.info("Phase 1: Writing to Redis...")
            redis_start_time = time.perf_counter()
            message_ids = await self.write_to_redis_parallel(payloads)
            redis_end_time = time.perf_counter()
            
            redis_write_duration = redis_end_time - redis_start_time
            actual_write_rps = len(message_ids) / redis_write_duration if redis_write_duration > 0 else 0
            
            logger.info(f"Redis write completed: {len(message_ids)} messages in {redis_write_duration:.3f}s")
            
            # Phase 2: Wait for processing (1 second)
            logger.info("Phase 2: Waiting for database processing...")
            await asyncio.sleep(1.0)
            
            # Phase 3: Count database records
            logger.info("Phase 3: Counting database records...")
            test_end_time = datetime.now()
            db_record_count = await self.count_database_records(test_start_time, test_end_time)
            
            # Calculate metrics
            success_rate = (db_record_count / len(payloads)) * 100 if payloads else 0
            total_test_duration = time.perf_counter() - redis_start_time
            
            results = {
                "test_config": {
                    "target_rps": self.target_rps,
                    "test_duration_seconds": self.test_duration_seconds,
                    "total_messages_sent": len(payloads)
                },
                "redis_metrics": {
                    "messages_written": len(message_ids),
                    "write_duration_seconds": redis_write_duration,
                    "actual_write_rps": actual_write_rps,
                    "redis_success_rate": (len(message_ids) / len(payloads)) * 100 if payloads else 0
                },
                "database_metrics": {
                    "records_in_db": db_record_count,
                    "db_success_rate": success_rate,
                    "processing_efficiency": f"{db_record_count}/{len(message_ids)}" if message_ids else "0/0"
                },
                "overall_metrics": {
                    "total_test_duration_seconds": total_test_duration,
                    "end_to_end_success_rate": success_rate,
                    "messages_per_second_processed": db_record_count / total_test_duration if total_test_duration > 0 else 0
                }
            }
            
            # Log results
            logger.info("=== PERFORMANCE TEST RESULTS ===")
            logger.info(f"Target: {self.target_rps} RPS, Sent: {len(payloads)} messages")
            logger.info(f"Redis: {len(message_ids)} written in {redis_write_duration:.3f}s ({actual_write_rps:.1f} RPS)")
            logger.info(f"Database: {db_record_count} records found ({success_rate:.1f}% success rate)")
            logger.info(f"Total duration: {total_test_duration:.3f}s")
            
            # Note: Test data preserved for inspection
            
            return results
            
        finally:
            await redis_manager.disconnect()
            await db_manager.disconnect()


# Run test if executed directly
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        test = PerformanceLoadTest(target_rps=10000, test_duration_seconds=1)
        results = await test.run_performance_test()
        
        print("\n" + "="*50)
        print("FINAL PERFORMANCE TEST RESULTS")
        print("="*50)
        print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(main())