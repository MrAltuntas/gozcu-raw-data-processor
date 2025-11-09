"""Redis stream consumer service"""
import logging
from typing import Optional
import redis.asyncio as redis

from src.core.redis_client import redis_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class RedisConsumer:
    """Redis Stream consumer using XREADGROUP"""

    def __init__(self):
        """Initialize Redis consumer"""
        self._client: Optional[redis.Redis] = None
        self._stream_key = settings.redis.stream_key
        self._consumer_group = settings.redis.consumer_group
        self._consumer_name = settings.redis.consumer_name
        self._pending_message_ids: list[str] = []

    async def initialize(self) -> None:
        """Initialize consumer and create consumer group if not exists"""
        try:
            self._client = redis_manager.get_client()

            # Create consumer group if it doesn't exist
            try:
                await self._client.xgroup_create(
                    name=self._stream_key,
                    groupname=self._consumer_group,
                    id="0",
                    mkstream=True
                )
                logger.info(
                    f"Created consumer group '{self._consumer_group}' "
                    f"for stream '{self._stream_key}'"
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(
                        f"Consumer group '{self._consumer_group}' already exists"
                    )
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            raise

    async def read_stream(self, count: int = 10, block_ms: int = 1000) -> list[dict]:
        """
        Read messages from Redis Stream using XREADGROUP

        Args:
            count: Maximum number of messages to read
            block_ms: Blocking timeout in milliseconds (0 for non-blocking)

        Returns:
            list[dict]: List of messages with their IDs and data

        Raises:
            RuntimeError: If consumer is not initialized
            redis.RedisError: If Redis operation fails
        """
        if self._client is None:
            raise RuntimeError("Consumer not initialized. Call initialize() first.")

        try:
            # XREADGROUP GROUP group consumer [COUNT count] [BLOCK milliseconds] STREAMS key >
            response = await self._client.xreadgroup(
                groupname=self._consumer_group,
                consumername=self._consumer_name,
                streams={self._stream_key: ">"},
                count=count,
                block=block_ms
            )

            if not response:
                logger.debug("No new messages in stream")
                return []

            # Parse response: [(stream_name, [(message_id, data), ...])]
            messages = []
            for stream_name, stream_messages in response:
                for message_id, data in stream_messages:
                    # Store message ID for later acknowledgment
                    self._pending_message_ids.append(message_id)

                    messages.append({
                        "id": message_id,
                        "stream": stream_name,
                        "data": data
                    })

            logger.info(f"Read {len(messages)} messages from stream '{self._stream_key}'")
            return messages

        except redis.RedisError as e:
            logger.error(f"Redis error while reading stream: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while reading stream: {e}")
            raise

    async def acknowledge(self, message_ids: list[str]) -> int:
        """
        Acknowledge processed messages using XACK

        Args:
            message_ids: List of message IDs to acknowledge

        Returns:
            int: Number of messages successfully acknowledged

        Raises:
            RuntimeError: If consumer is not initialized
            redis.RedisError: If Redis operation fails
        """
        if self._client is None:
            raise RuntimeError("Consumer not initialized. Call initialize() first.")

        if not message_ids:
            logger.debug("No message IDs to acknowledge")
            return 0

        try:
            # XACK key group id [id ...]
            ack_count = await self._client.xack(
                self._stream_key,
                self._consumer_group,
                *message_ids
            )

            # Remove acknowledged IDs from pending list
            self._pending_message_ids = [
                msg_id for msg_id in self._pending_message_ids
                if msg_id not in message_ids
            ]

            logger.info(
                f"Acknowledged {ack_count}/{len(message_ids)} messages "
                f"in stream '{self._stream_key}'"
            )
            return ack_count

        except redis.RedisError as e:
            logger.error(f"Redis error while acknowledging messages: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while acknowledging messages: {e}")
            raise

    async def get_pending_info(self) -> dict:
        """
        Get information about pending messages for this consumer

        Returns:
            dict: Pending messages information
        """
        if self._client is None:
            raise RuntimeError("Consumer not initialized. Call initialize() first.")

        try:
            # XPENDING key group [start end count] [consumer]
            pending = await self._client.xpending_range(
                name=self._stream_key,
                groupname=self._consumer_group,
                min="-",
                max="+",
                count=100,
                consumername=self._consumer_name
            )

            return {
                "count": len(pending),
                "messages": pending,
                "local_pending_count": len(self._pending_message_ids)
            }

        except redis.RedisError as e:
            logger.error(f"Redis error while getting pending info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting pending info: {e}")
            raise

    @property
    def pending_message_ids(self) -> list[str]:
        """Get list of locally tracked pending message IDs"""
        return self._pending_message_ids.copy()

    @property
    def pending_count(self) -> int:
        """Get count of locally tracked pending messages"""
        return len(self._pending_message_ids)


# Singleton instance
redis_consumer = RedisConsumer()
