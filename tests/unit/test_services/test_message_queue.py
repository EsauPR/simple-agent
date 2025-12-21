"""Tests for MessageQueue service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.message_queue import MessageQueue, QueuedMessage


@pytest.mark.asyncio
class TestMessageQueue:
    """Tests for MessageQueue service"""

    async def test_enqueue_message(self):
        """Test enqueuing a message"""
        # Reset singleton for clean test
        MessageQueue._instance = None
        MessageQueue._queue = None

        queue = MessageQueue()

        # Clear any existing messages
        while queue.size() > 0:
            await queue.dequeue_message()

        # Enqueue a message
        await queue.enqueue_message("+1234567890", "Test message")

        # Verify message was enqueued
        assert queue.size() == 1

    async def test_dequeue_message(self):
        """Test dequeuing a message"""
        # Reset singleton for clean test
        MessageQueue._instance = None
        MessageQueue._queue = None

        queue = MessageQueue()

        # Clear any existing messages
        while queue.size() > 0:
            await queue.dequeue_message()

        # Enqueue a message
        await queue.enqueue_message("+1234567890", "Test message")

        # Dequeue the message
        message = await queue.dequeue_message()

        # Verify message was dequeued correctly
        assert message is not None
        assert message.phone_number == "+1234567890"
        assert message.message == "Test message"
        assert isinstance(message.timestamp, datetime)
        assert queue.size() == 0

    async def test_dequeue_empty_queue(self):
        """Test dequeuing from empty queue returns None"""
        # Reset singleton for clean test
        MessageQueue._instance = None
        MessageQueue._queue = None

        queue = MessageQueue()

        # Try to dequeue from empty queue
        message = await queue.dequeue_message()

        # Verify None is returned
        assert message is None

    async def test_queue_size(self):
        """Test queue size tracking"""
        # Reset singleton for clean test
        MessageQueue._instance = None
        MessageQueue._queue = None

        queue = MessageQueue()

        # Clear any existing messages
        while queue.size() > 0:
            await queue.dequeue_message()

        # Initially empty
        assert queue.size() == 0

        # Enqueue multiple messages
        await queue.enqueue_message("+1111111111", "Message 1")
        assert queue.size() == 1

        await queue.enqueue_message("+2222222222", "Message 2")
        assert queue.size() == 2

        # Dequeue one
        await queue.dequeue_message()
        assert queue.size() == 1

    async def test_queued_message_dataclass(self):
        """Test QueuedMessage dataclass structure"""
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Test message",
            timestamp=datetime.now()
        )

        assert message.phone_number == "+1234567890"
        assert message.message == "Test message"
        assert isinstance(message.timestamp, datetime)

    async def test_singleton_pattern(self):
        """Test that MessageQueue is a singleton"""
        # Reset singleton
        MessageQueue._instance = None
        MessageQueue._queue = None

        queue1 = MessageQueue()
        queue2 = MessageQueue()

        # Both should be the same instance
        assert queue1 is queue2

        # Enqueue in one, should be visible in the other
        await queue1.enqueue_message("+1234567890", "Test")
        assert queue2.size() == 1
