"""Integration tests for chat router"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.database.connection import get_db
from src.services.agent.chat_service import ChatService


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client with overridden database"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestChatRouter:
    """Tests for chat router"""

    async def test_process_message_endpoint(self, client: TestClient, test_db):
        """Test process message endpoint"""
        with patch.object(ChatService, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = "Test response"

            request_data = {
                "message": "Hello",
                "phone_number": "+1234567890"
            }

            response = client.post("/api/v1/chat/message", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Test response"
            assert data["phone_number"] == "+1234567890"
            mock_process.assert_called_once_with("+1234567890", "Hello")

    async def test_twilio_webhook_valid_signature(self, client: TestClient, test_db, mock_twilio_validator):
        """Test Twilio webhook with valid signature"""
        with patch.object(ChatService, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = "Test response"

            form_data = {
                "From": "whatsapp:+1234567890",
                "Body": "Hello"
            }

            response = client.post(
                "/api/v1/chat/webhooks/twilio",
                data=form_data,
                headers={"X-Twilio-Signature": "valid_signature"}
            )

            assert response.status_code == 200
            assert "application/xml" in response.headers["content-type"]
            assert "Test response" in response.text

    async def test_twilio_webhook_invalid_signature(self, client: TestClient, test_db):
        """Test Twilio webhook with invalid signature"""
        with patch("src.routers.chat.RequestValidator") as mock_validator:
            mock_instance = mock_validator.return_value
            mock_instance.validate = lambda *args: False

            form_data = {
                "From": "whatsapp:+1234567890",
                "Body": "Hello"
            }

            # Set webhook secret to enable validation
            with patch("src.config.settings.TWILIO_WEBHOOK_SECRET", "test_secret"):
                response = client.post(
                    "/api/v1/chat/webhooks/twilio",
                    data=form_data,
                    headers={"X-Twilio-Signature": "invalid_signature"}
                )

                assert response.status_code == 403

    async def test_twilio_webhook_missing_fields(self, client: TestClient, test_db):
        """Test Twilio webhook with missing fields"""
        # Disable webhook secret validation for this test
        with patch("src.config.settings.TWILIO_WEBHOOK_SECRET", None):
            form_data = {
                "Body": "Hello"
                # Missing From
            }

            response = client.post("/api/v1/chat/webhooks/twilio", data=form_data)

            assert response.status_code == 400

    async def test_twilio_webhook_response_format(self, client: TestClient, test_db):
        """Test Twilio webhook response format"""
        # Disable webhook secret validation for this test
        with patch("src.config.settings.TWILIO_WEBHOOK_SECRET", None), \
             patch.object(ChatService, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = "Test response"

            form_data = {
                "From": "whatsapp:+1234567890",
                "Body": "Hello"
            }

            response = client.post("/api/v1/chat/webhooks/twilio", data=form_data)

            assert response.status_code == 200
            assert "application/xml" in response.headers["content-type"]
            # Should be TwiML format
            assert "<?xml" in response.text or "<Response>" in response.text
