"""Simple test to write camera events to Redis stream."""

import asyncio
import json
import logging
from typing import List

from src.core.redis_client import redis_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class TestRedisWriter:
    """Simple test to write camera events to Redis stream."""

    @classmethod
    def get_test_payloads(cls) -> List[dict]:
        """Get sample test payloads."""
        base_time = "2025-11-12T14:30:45.123456"
        
        return [
            # Payload 1: Multiple detections
            {
                "cameraID": 1,
                "eventDate": base_time,
                "detectedObjects": [
                    {
                        "className": 0,
                        "confidence": 85,
                        "photoUrl": "kapi_saved_images/person_85_1730901045.jpg",
                        "coordinateX": 450,
                        "coordinateY": 320,
                        "regionID": [1, 3]
                    },
                    {
                        "className": 2,
                        "confidence": 92,
                        "photoUrl": "kapi_saved_images/car_92_1730901045.jpg",
                        "coordinateX": 120,
                        "coordinateY": 580,
                        "regionID": [2]
                    }
                ]
            },
            # Payload 2: Single detection
            {
                "cameraID": 2,
                "eventDate": "2025-11-12T14:31:00.123456",
                "detectedObjects": [
                    {
                        "className": 3,
                        "confidence": 90,
                        "photoUrl": "kapi_saved_images/car_92_17309012135.jpg",
                        "coordinateX": 10,
                        "coordinateY": 50,
                        "regionID": []
                    }
                ]
            },
            # Payload 3: No detections
            {
                "cameraID": 1,
                "eventDate": "2025-11-12T14:31:15.123456",
                "detectedObjects": []
            },
            # Payload 4: Different camera with detection
            {
                "cameraID": 3,
                "eventDate": "2025-11-12T14:31:30.123456",
                "detectedObjects": [
                    {
                        "className": 1,
                        "confidence": 78,
                        "photoUrl": "garage_saved_images/bicycle_78_1730901090.jpg",
                        "coordinateX": 200,
                        "coordinateY": 150,
                        "regionID": [4, 5]
                    }
                ]
            },
            # Payload 5: Another no detection event
            {
                "cameraID": 2,
                "eventDate": "2025-11-12T14:31:45.123456",
                "detectedObjects": []
            }
        ]

    async def write_to_redis_stream(self, payloads: List[dict]) -> List[str]:
        """
        Write test payloads to Redis stream.
        
        Args:
            payloads: List of test payloads to write
            
        Returns:
            List of message IDs written to Redis
        """
        client = redis_manager.get_client()
        message_ids = []
        
        for payload in payloads:
            # Convert payload to Redis stream format (all values must be strings)
            redis_payload = {}
            for key, value in payload.items():
                if isinstance(value, (dict, list)):
                    redis_payload[key] = json.dumps(value)
                else:
                    redis_payload[key] = str(value)
            
            # Add to stream using XADD
            message_id = await client.xadd(
                name=settings.redis.stream_key,
                fields=redis_payload
            )
            message_ids.append(message_id)
            logger.info(f"Added message {message_id} to Redis stream")
        
        return message_ids

    async def test_write_to_redis(self):
        """Write test payloads to Redis stream and let the running project process them."""
        
        # Initialize Redis connection
        await redis_manager.connect()
        
        try:
            # Get test payloads
            test_payloads = self.get_test_payloads()
            logger.info(f"Writing {len(test_payloads)} test payloads to Redis stream")
            
            # Write test data to Redis
            message_ids = await self.write_to_redis_stream(test_payloads)
            
            logger.info(f"✅ Successfully wrote {len(message_ids)} messages to Redis stream '{settings.redis.stream_key}'")
            logger.info("The running project will automatically process these messages and write them to the database.")
            
            for i, (payload, msg_id) in enumerate(zip(test_payloads, message_ids), 1):
                detection_count = len(payload["detectedObjects"])
                logger.info(f"Message {i}: Camera {payload['cameraID']} - {detection_count} detections - ID: {msg_id}")
            
        finally:
            # Disconnect
            await redis_manager.disconnect()


# Run test if executed directly
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        test = TestRedisWriter()
        await test.test_write_to_redis()
    
    asyncio.run(main())