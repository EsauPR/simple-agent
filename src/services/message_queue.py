"""Message queue service for asynchronous message processing"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class QueuedMessage:
    """Represents a message queued for processing"""
    phone_number: str
    message: str
    timestamp: datetime


class MessageQueue:
    """Singleton message queue using asyncio.Queue"""
    _instance: Optional['MessageQueue'] = None
    _queue: Optional[asyncio.Queue] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._queue = asyncio.Queue()
        return cls._instance

    async def enqueue_message(self, phone_number: str, message: str) -> None:
        """Add a message to the queue"""
        queued_message = QueuedMessage(
            phone_number=phone_number,
            message=message,
            timestamp=datetime.now()
        )
        await self._queue.put(queued_message)
        logger.debug(f"Message enqueued for {phone_number}: {message[:50]}...")

    async def dequeue_message(self) -> Optional[QueuedMessage]:
        """Get a message from the queue. Returns None if queue is empty."""
        try:
            # Use timeout to avoid blocking indefinitely
            message = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            return message
        except asyncio.TimeoutError:
            return None

    def size(self) -> int:
        """Get the current size of the queue"""
        return self._queue.qsize()


message_queue = MessageQueue()
