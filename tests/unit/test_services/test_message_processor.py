"""Tests for MessageProcessor service"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.message_processor import MessageProcessor
from src.services.message_queue import QueuedMessage


@pytest.mark.asyncio
class TestMessageProcessor:
    """Tests for MessageProcessor service"""

    async def test_process_single_message_success(self, test_db):
        """Test successful processing of a single message"""
        processor = MessageProcessor()

        # Create test message
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Hello",
            timestamp=datetime.now()
        )

        # Mock dependencies
        with patch('src.services.message_processor.ChatService') as mock_chat_service_class, \
             patch('src.services.message_processor.twilio_service') as mock_twilio_service:

            # Setup ChatService mock
            mock_chat_service = MagicMock()
            mock_chat_service.process_message = AsyncMock(return_value="Test response")
            mock_chat_service_class.return_value = mock_chat_service

            # Setup TwilioService mock
            mock_twilio_service.send_message.return_value = True

            # Process message
            await processor.process_single_message(message, test_db)

            # Verify ChatService was called correctly
            mock_chat_service.process_message.assert_called_once_with("+1234567890", "Hello")

            # Verify TwilioService was called with response
            mock_twilio_service.send_message.assert_called_once_with("+1234567890", "Test response")

    async def test_process_single_message_twilio_send_failure(self, test_db):
        """Test processing when Twilio send fails"""
        processor = MessageProcessor()

        # Create test message
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Hello",
            timestamp=datetime.now()
        )

        # Mock dependencies
        with patch('src.services.message_processor.ChatService') as mock_chat_service_class, \
             patch('src.services.message_processor.twilio_service') as mock_twilio_service:

            # Setup ChatService mock
            mock_chat_service = MagicMock()
            mock_chat_service.process_message = AsyncMock(return_value="Test response")
            mock_chat_service_class.return_value = mock_chat_service

            # Setup TwilioService mock - first call fails, second (error message) succeeds
            mock_twilio_service.send_message.side_effect = [False, True]

            # Process message
            await processor.process_single_message(message, test_db)

            # Verify TwilioService was called twice (response + error message)
            assert mock_twilio_service.send_message.call_count == 2
            # First call with response
            assert mock_twilio_service.send_message.call_args_list[0][0] == ("+1234567890", "Test response")
            # Second call with error message
            assert "Lo siento" in mock_twilio_service.send_message.call_args_list[1][0][1]

    async def test_process_single_message_processing_exception(self, test_db):
        """Test processing when ChatService raises exception"""
        processor = MessageProcessor()

        # Create test message
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Hello",
            timestamp=datetime.now()
        )

        # Mock dependencies
        with patch('src.services.message_processor.ChatService') as mock_chat_service_class, \
             patch('src.services.message_processor.twilio_service') as mock_twilio_service:

            # Setup ChatService mock to raise exception
            mock_chat_service = MagicMock()
            mock_chat_service.process_message = AsyncMock(side_effect=Exception("Processing error"))
            mock_chat_service_class.return_value = mock_chat_service

            # Setup TwilioService mock
            mock_twilio_service.send_message.return_value = True

            # Process message
            await processor.process_single_message(message, test_db)

            # Verify error message was sent
            mock_twilio_service.send_message.assert_called_once()
            assert "Lo siento" in mock_twilio_service.send_message.call_args[0][1]

    async def test_process_single_message_error_send_failure(self, test_db):
        """Test processing when both processing and error message sending fail"""
        processor = MessageProcessor()

        # Create test message
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Hello",
            timestamp=datetime.now()
        )

        # Mock dependencies
        with patch('src.services.message_processor.ChatService') as mock_chat_service_class, \
             patch('src.services.message_processor.twilio_service') as mock_twilio_service:

            # Setup ChatService mock to raise exception
            mock_chat_service = MagicMock()
            mock_chat_service.process_message = AsyncMock(side_effect=Exception("Processing error"))
            mock_chat_service_class.return_value = mock_chat_service

            # Setup TwilioService mock to fail
            mock_twilio_service.send_message.side_effect = Exception("Twilio error")

            # Process message - should not raise exception
            await processor.process_single_message(message, test_db)

            # Verify attempt was made to send error message
            mock_twilio_service.send_message.assert_called_once()

    async def test_start_stop(self):
        """Test starting and stopping the processor"""
        processor = MessageProcessor()

        # Initially not running
        assert processor._running is False

        # Start processor
        await processor.start()
        assert processor._running is True
        assert processor._task is not None

        # Stop processor
        await processor.stop()
        assert processor._running is False

    async def test_start_when_already_running(self):
        """Test starting processor when already running"""
        processor = MessageProcessor()

        # Start processor
        await processor.start()
        assert processor._running is True

        # Try to start again - should not create new task
        task_before = processor._task
        await processor.start()
        assert processor._task is task_before

        # Cleanup
        await processor.stop()

    async def test_stop_when_not_running(self):
        """Test stopping processor when not running"""
        processor = MessageProcessor()

        # Stop when not running - should not raise exception
        await processor.stop()
        assert processor._running is False

    @patch('src.services.message_processor.message_queue')
    @patch('src.services.message_processor.AsyncSessionLocal')
    async def test_process_message_queue_with_message(self, mock_session_local, mock_queue):
        """Test message queue processing when message is available"""
        processor = MessageProcessor()
        processor._running = True

        # Create test message
        message = QueuedMessage(
            phone_number="+1234567890",
            message="Hello",
            timestamp=datetime.now()
        )

        # Mock queue to return message then None (to exit loop)
        mock_queue.dequeue_message = AsyncMock(side_effect=[message, None])

        # Mock database session
        mock_db = MagicMock()
        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_session_local.return_value = mock_session_context

        # Mock process_single_message
        with patch.object(processor, 'process_single_message', new_callable=AsyncMock) as mock_process:
            # Start processor and let it run briefly
            task = asyncio.create_task(processor.process_message_queue())

            # Wait a bit for processing
            await asyncio.sleep(0.3)

            # Stop processor
            processor._running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify message was dequeued
            assert mock_queue.dequeue_message.call_count >= 1

    @patch('src.services.message_processor.message_queue')
    async def test_process_message_queue_empty(self, mock_queue):
        """Test message queue processing when queue is empty"""
        processor = MessageProcessor()

        # Mock queue to always return None
        mock_queue.dequeue_message = AsyncMock(return_value=None)

        # Start processor and let it run briefly
        processor._running = True
        task = asyncio.create_task(processor.process_message_queue())

        # Wait a bit for processing
        await asyncio.sleep(0.3)

        # Stop processor
        processor._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify queue was checked
        assert mock_queue.dequeue_message.call_count >= 1
