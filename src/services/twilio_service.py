"""Twilio service for sending messages via Twilio API"""
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from src.config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for sending messages via Twilio API"""

    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.phone_number = settings.TWILIO_PHONE_NUMBER

    def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send a message via Twilio API

        Args:
            phone_number: Recipient phone number (with country code, e.g., +521234567890)
            message: Message content to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            if not phone_number.startswith("whatsapp:"):
                whatsapp_number = f"whatsapp:{phone_number}"
            else:
                whatsapp_number = phone_number

            message_obj = self.client.messages.create(
                body=message,
                from_=f"whatsapp:{self.phone_number}",
                to=whatsapp_number
            )

            logger.info(f"Message sent successfully to {phone_number}. SID: {message_obj.sid}")
            return True

        except TwilioException as e:
            logger.error(f"Twilio error sending message to {phone_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to {phone_number}: {e}", exc_info=True)
            return False


twilio_service = TwilioService()
