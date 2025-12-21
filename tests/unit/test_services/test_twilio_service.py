"""Tests for TwilioService"""
import pytest
from unittest.mock import MagicMock, patch
from twilio.base.exceptions import TwilioException

from src.services.twilio_service import TwilioService


@pytest.mark.asyncio
class TestTwilioService:
    """Tests for TwilioService"""

    @patch('src.services.twilio_service.Client')
    @patch('src.services.twilio_service.settings')
    def test_send_message_success(self, mock_settings, mock_client_class):
        """Test successful message sending"""
        # Setup mocks
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_settings.TWILIO_PHONE_NUMBER = "+1234567890"

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM1234567890"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        # Create service
        service = TwilioService()

        # Send message
        result = service.send_message("+9876543210", "Test message")

        # Verify success
        assert result is True
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["body"] == "Test message"
        assert call_kwargs["from_"] == "whatsapp:+1234567890"
        assert call_kwargs["to"] == "whatsapp:+9876543210"

    @patch('src.services.twilio_service.Client')
    @patch('src.services.twilio_service.settings')
    def test_send_message_with_whatsapp_prefix(self, mock_settings, mock_client_class):
        """Test message sending with whatsapp: prefix already in phone number"""
        # Setup mocks
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_settings.TWILIO_PHONE_NUMBER = "+1234567890"

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM1234567890"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        # Create service
        service = TwilioService()

        # Send message with whatsapp: prefix
        result = service.send_message("whatsapp:+9876543210", "Test message")

        # Verify success and that prefix wasn't duplicated
        assert result is True
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["to"] == "whatsapp:+9876543210"

    @patch('src.services.twilio_service.Client')
    @patch('src.services.twilio_service.settings')
    def test_send_message_twilio_exception(self, mock_settings, mock_client_class):
        """Test message sending with TwilioException"""
        # Setup mocks
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_settings.TWILIO_PHONE_NUMBER = "+1234567890"

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = TwilioException("Twilio error")
        mock_client_class.return_value = mock_client

        # Create service
        service = TwilioService()

        # Send message
        result = service.send_message("+9876543210", "Test message")

        # Verify failure
        assert result is False

    @patch('src.services.twilio_service.Client')
    @patch('src.services.twilio_service.settings')
    def test_send_message_generic_exception(self, mock_settings, mock_client_class):
        """Test message sending with generic exception"""
        # Setup mocks
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_settings.TWILIO_PHONE_NUMBER = "+1234567890"

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        # Create service
        service = TwilioService()

        # Send message
        result = service.send_message("+9876543210", "Test message")

        # Verify failure
        assert result is False
