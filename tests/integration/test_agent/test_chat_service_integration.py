"""Integration tests for ChatService"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.agent.chat_service import ChatService
from src.config import settings


@pytest.mark.asyncio
class TestChatServiceIntegration:
    """Integration tests for ChatService"""

    async def test_process_message_complete_flow(self, test_db):
        """Test complete message processing flow"""
        service = ChatService(test_db)

        # Mock the agent
        mock_result = {
            "messages": [
                MagicMock(content="Test response from agent")
            ]
        }

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.return_value = mock_result

            response = await service.process_message("+1234567890", "Hello")

            assert response == "Test response from agent"
            mock_agent.assert_called_once()
            # Verify thread_id was used
            call_args = mock_agent.call_args
            # call_args is (args, kwargs), config is passed as second positional arg
            assert len(call_args[0]) >= 2
            assert call_args[0][1]["configurable"]["thread_id"] == "+1234567890"

    async def test_response_length_limit(self, test_db):
        """Test that response is truncated if exceeds limit"""
        service = ChatService(test_db)

        # Create a long response
        long_response = "A" * (settings.MAX_RESPONSE_LENGTH + 100)
        mock_result = {
            "messages": [
                MagicMock(content=long_response)
            ]
        }

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.return_value = mock_result

            response = await service.process_message("+1234567890", "Test")

            assert len(response) <= settings.MAX_RESPONSE_LENGTH

    async def test_response_truncation_at_sentence(self, test_db):
        """Test that truncation happens at sentence boundary"""
        service = ChatService(test_db)

        # Create response that exceeds limit but has sentences
        long_response = "Sentence 1. " * 200  # Will exceed limit
        mock_result = {
            "messages": [
                MagicMock(content=long_response)
            ]
        }

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.return_value = mock_result

            response = await service.process_message("+1234567890", "Test")

            assert len(response) <= settings.MAX_RESPONSE_LENGTH
            # Should end at a sentence boundary if possible
            if len(response) < len(long_response):
                # Check it ends with a period or is truncated intelligently
                assert response[-1] in ['.', '\n'] or len(response) == settings.MAX_RESPONSE_LENGTH

    async def test_conversation_context_persistence(self, test_db):
        """Test that conversation context persists across messages"""
        service = ChatService(test_db)

        # First message
        mock_result_1 = {
            "messages": [
                MagicMock(content="First response")
            ]
        }

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.return_value = mock_result_1

            await service.process_message("+1234567890", "First message")

            # Second message - should use same thread_id
            mock_result_2 = {
                "messages": [
                    MagicMock(content="Second response")
                ]
            }
            mock_agent.return_value = mock_result_2

            await service.process_message("+1234567890", "Second message")

            # Verify both calls used the same thread_id
            assert mock_agent.call_count == 2
            # call_args is (args, kwargs), config is passed as second positional arg
            first_call_thread = mock_agent.call_args_list[0][0][1]["configurable"]["thread_id"]
            second_call_thread = mock_agent.call_args_list[1][0][1]["configurable"]["thread_id"]
            assert first_call_thread == second_call_thread == "+1234567890"

    async def test_error_handling(self, test_db):
        """Test error handling in process_message"""
        service = ChatService(test_db)

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.side_effect = Exception("Test error")

            response = await service.process_message("+1234567890", "Test")

            assert "problema procesando" in response.lower() or "intentar de nuevo" in response.lower()

    async def test_empty_messages_handling(self, test_db):
        """Test handling when agent returns no messages"""
        service = ChatService(test_db)

        mock_result = {
            "messages": []
        }

        with patch.object(service.agent, 'ainvoke', new_callable=AsyncMock) as mock_agent:
            mock_agent.return_value = mock_result

            response = await service.process_message("+1234567890", "Test")

            assert "no pude procesar" in response.lower() or "reformular" in response.lower()
