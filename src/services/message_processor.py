"""Message processor service for processing queued messages"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.message_queue import message_queue, QueuedMessage
from src.services.twilio_service import twilio_service
from src.services.agent.chat_service import ChatService
from src.database.connection import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Processes messages from the queue"""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def process_single_message(self, message: QueuedMessage, db: AsyncSession) -> None:
        """
        Process a single message from the queue

        Args:
            message: The queued message to process
            db: Database session for ChatService
        """
        try:
            logger.info(f"Processing message for {message.phone_number}: {message.message[:50]}...")

            # Process message using ChatService
            chat_service = ChatService(db)
            response_text = await chat_service.process_message(
                message.phone_number,
                message.message
            )

            logger.debug(f"Generated response for {message.phone_number}: {response_text[:50]}...")

            # Send response via Twilio
            success = twilio_service.send_message(message.phone_number, response_text)

            if success:
                logger.info(f"Successfully processed and sent response to {message.phone_number}")
            else:
                logger.error(f"Failed to send response to {message.phone_number}")
                # Send error message to user
                error_message = "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?"
                twilio_service.send_message(message.phone_number, error_message)

        except Exception as e:
            logger.error(
                f"Error processing message for {message.phone_number}: {e}",
                exc_info=True
            )
            # Send error message to user
            try:
                error_message = "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?"
                twilio_service.send_message(message.phone_number, error_message)
            except Exception as send_error:
                logger.error(f"Failed to send error message to {message.phone_number}: {send_error}")

    async def process_message_queue(self) -> None:
        """Background task that processes messages from the queue every 2 seconds"""
        logger.info("Message processor cron job started")

        while self._running:
            try:
                # Try to dequeue a message
                message = await message_queue.dequeue_message()

                if message:
                    # Create a database session for processing
                    async with AsyncSessionLocal() as db:
                        # Process the message
                        await self.process_single_message(message, db)
                # If no message, just continue to next iteration

            except Exception as e:
                logger.error(f"Error in message processor loop: {e}", exc_info=True)

            # Sleep for 2 seconds before next iteration
            await asyncio.sleep(2)

        logger.info("Message processor cron job stopped")

    async def start(self) -> None:
        """Start the message processor background task"""
        if self._running:
            logger.warning("Message processor is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self.process_message_queue())
        logger.info("Message processor started")

    async def stop(self) -> None:
        """Stop the message processor background task"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Message processor task cancelled")

        logger.info("Message processor stopped")


# Singleton instance
message_processor = MessageProcessor()
