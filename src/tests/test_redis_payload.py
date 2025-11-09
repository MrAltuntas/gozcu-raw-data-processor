"""
Test script for Redis payload processing
Tests the microservice with expected payload format from other services
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

import redis.asyncio as redis

from src.config.settings import settings


logger = logging.getLogger(__name__)


class PayloadTester:
    """Test Redis stream payload processing with realistic data"""
    
    def __init__(self):
        """Initialize test client"""
        self.redis_client: redis.Redis = None
        self.stream_key = settings.redis.stream_key
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            decode_responses=True
        )
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Redis connection established")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection closed")
    
    def generate_test_payloads(self) -> List[Dict[str, Any]]:
        """Generate test payloads matching the expected format"""
        
        base_time = datetime.now()
        
        payloads = [
            # Payload 1: Multiple objects detected
            {
                "cameraID": 1,
                "eventDate": base_time.isoformat(),
                "detectedObjects": [
                    {
                        "className": 0,  # person
                        "confidence": 85,
                        "photoUrl": "kapi_saved_images/person_85_1730901045.jpg",
                        "coordinateX": 450,
                        "coordinateY": 320,
                        "regionID": [1, 3]
                    },
                    {
                        "className": 2,  # car
                        "confidence": 92,
                        "photoUrl": "kapi_saved_images/car_92_1730901045.jpg",
                        "coordinateX": 120,
                        "coordinateY": 580,
                        "regionID": [2]
                    },
                    {
                        "className": 3,  # motorcycle
                        "confidence": 90,
                        "photoUrl": "kapi_saved_images/motorcycle_90_1730901045.jpg",
                        "coordinateX": 10,
                        "coordinateY": 50,
                        "regionID": []
                    }
                ]
            },
            
            # Payload 2: Single object detected
            {
                "cameraID": 2,
                "eventDate": base_time.isoformat(),
                "detectedObjects": [
                    {
                        "className": 0,  # person
                        "confidence": 95,
                        "photoUrl": "kapi_saved_images/person_95_1730901046.jpg",
                        "coordinateX": 640,
                        "coordinateY": 480,
                        "regionID": [1]
                    }
                ]
            },
            
            # Payload 3: No objects detected
            {
                "cameraID": 3,
                "eventDate": base_time.isoformat(),
                "detectedObjects": []
            },
            
            # Payload 4: High confidence detections
            {
                "cameraID": 1,
                "eventDate": base_time.isoformat(),
                "detectedObjects": [
                    {
                        "className": 1,  # bicycle
                        "confidence": 98,
                        "photoUrl": "kapi_saved_images/bicycle_98_1730901047.jpg",
                        "coordinateX": 200,
                        "coordinateY": 150,
                        "regionID": [2, 4]
                    }
                ]
            },
            
            # Payload 5: Low confidence detection
            {
                "cameraID": 4,
                "eventDate": base_time.isoformat(),
                "detectedObjects": [
                    {
                        "className": 5,  # bus
                        "confidence": 65,
                        "photoUrl": "kapi_saved_images/bus_65_1730901048.jpg",
                        "coordinateX": 800,
                        "coordinateY": 600,
                        "regionID": [3]
                    }
                ]
            }
        ]
        
        return payloads
    
    async def send_payload(self, payload: Dict[str, Any]) -> str:
        """Send a single payload to Redis stream"""
        
        # Convert payload to Redis stream format
        # Redis streams store data as field-value pairs
        stream_data = {}
        
        # Convert nested objects to JSON strings for Redis storage
        stream_data["cameraID"] = str(payload["cameraID"])
        stream_data["eventDate"] = payload["eventDate"]
        stream_data["detectedObjects"] = json.dumps(payload["detectedObjects"])
        
        # Send to Redis stream using XADD
        message_id = await self.redis_client.xadd(
            name=self.stream_key,
            fields=stream_data
        )
        
        return message_id
    
    async def test_single_payloads(self):
        """Test sending individual payloads"""
        logger.info("=" * 50)
        logger.info("TESTING INDIVIDUAL PAYLOADS")
        logger.info("=" * 50)
        
        payloads = self.generate_test_payloads()
        
        for i, payload in enumerate(payloads, 1):
            logger.info(f"Sending payload {i}/5...")
            logger.info(f"Camera ID: {payload['cameraID']}")
            logger.info(f"Objects detected: {len(payload['detectedObjects'])}")
            
            message_id = await self.send_payload(payload)
            logger.info(f"✓ Payload sent with message ID: {message_id}")
            
            # Small delay between sends
            await asyncio.sleep(0.1)
        
        logger.info("✅ All individual payloads sent successfully")
    
    async def test_high_volume(self, requests_per_second: int = 150, duration_seconds: int = 10):
        """Test high volume scenario - 150 requests/second"""
        logger.info("=" * 50)
        logger.info(f"TESTING HIGH VOLUME: {requests_per_second} req/sec for {duration_seconds}s")
        logger.info("=" * 50)
        
        payloads = self.generate_test_payloads()
        total_requests = requests_per_second * duration_seconds
        interval = 1.0 / requests_per_second
        
        logger.info(f"Total requests to send: {total_requests}")
        logger.info(f"Request interval: {interval:.4f} seconds")
        
        start_time = time.time()
        sent_count = 0
        
        for i in range(total_requests):
            # Cycle through test payloads
            payload = payloads[i % len(payloads)]
            
            # Update timestamp to current time
            payload["eventDate"] = datetime.now().isoformat()
            
            try:
                message_id = await self.send_payload(payload)
                sent_count += 1
                
                if sent_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = sent_count / elapsed
                    logger.info(f"Sent {sent_count}/{total_requests} messages (rate: {rate:.1f}/sec)")
                
            except Exception as e:
                logger.error(f"Error sending message {i+1}: {e}")
                continue
            
            # Maintain rate limiting
            await asyncio.sleep(interval)
        
        elapsed_time = time.time() - start_time
        actual_rate = sent_count / elapsed_time
        
        logger.info("=" * 50)
        logger.info("HIGH VOLUME TEST RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total sent: {sent_count}/{total_requests}")
        logger.info(f"Duration: {elapsed_time:.2f} seconds")
        logger.info(f"Actual rate: {actual_rate:.1f} requests/second")
        logger.info(f"Target rate: {requests_per_second} requests/second")
        logger.info(f"Success rate: {(sent_count/total_requests)*100:.1f}%")
        
        if actual_rate >= requests_per_second * 0.95:  # 95% of target rate
            logger.info("✅ High volume test PASSED")
        else:
            logger.warning("⚠️  High volume test performance below target")
    
    async def test_stream_info(self):
        """Get information about the Redis stream"""
        logger.info("=" * 50)
        logger.info("REDIS STREAM INFORMATION")
        logger.info("=" * 50)
        
        try:
            # Get stream info
            stream_info = await self.redis_client.xinfo_stream(self.stream_key)
            
            logger.info(f"Stream: {self.stream_key}")
            logger.info(f"Length: {stream_info.get('length', 0)} messages")
            logger.info(f"Groups: {stream_info.get('groups', 0)} consumer groups")
            logger.info(f"First entry ID: {stream_info.get('first-entry', ['N/A'])[0]}")
            logger.info(f"Last entry ID: {stream_info.get('last-entry', ['N/A'])[0]}")
            
            # Get consumer groups info
            try:
                groups = await self.redis_client.xinfo_groups(self.stream_key)
                for group in groups:
                    logger.info(f"Group '{group['name']}': {group['pending']} pending, {group['consumers']} consumers")
            except Exception as e:
                logger.info(f"No consumer groups found: {e}")
                
        except Exception as e:
            logger.warning(f"Could not get stream info: {e}")


async def main():
    """Main test function"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tester = PayloadTester()
    
    try:
        # Connect to Redis
        await tester.connect()
        
        # Show current stream info
        await tester.test_stream_info()
        
        # Test individual payloads
        await tester.test_single_payloads()
        
        # Wait a bit before high volume test
        await asyncio.sleep(2)
        
        # Test high volume scenario
        await tester.test_high_volume(requests_per_second=150, duration_seconds=5)
        
        # Final stream info
        await tester.test_stream_info()
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    """
    Usage:
        python src/tests/test_redis_payload.py
        
    Or from project root:
        python -m src.tests.test_redis_payload
    """
    print("🚀 Starting Redis Payload Test")
    print("Make sure Docker services are running: docker-compose up -d")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
    
    print("=" * 60)
    print("✅ Test completed")