import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.services.agent.chat_service import ChatService
from src.schemas.chat import ChatMessageRequest, ChatMessageResponse
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def process_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process a user message"""
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        request.phone_number,
        request.message
    )

    return ChatMessageResponse(
        response=response,
        phone_number=request.phone_number
    )


@router.post("/webhooks/twilio")
async def twilio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Twilio webhook for WhatsApp"""
    # Validate Twilio signature
    if settings.TWILIO_WEBHOOK_SECRET:
        validator = RequestValidator(settings.TWILIO_WEBHOOK_SECRET)
        url = str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")
        params = dict(await request.form())
        logger.info("Validating Twilio signature")
        if not validator.validate(url, params, signature):
            logger.error(f"Invalid Twilio signature: {url}, {params}, {signature}")
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # Get data from the request
    form_data = await request.form()
    phone_number = form_data.get("From", "").replace("whatsapp:", "")
    user_message = form_data.get("Body", "")

    if not phone_number or not user_message:
        raise HTTPException(status_code=400, detail="Missing From or Body")

    # Process message
    chat_service = ChatService(db)
    response_text = await chat_service.process_message(phone_number, user_message)

    logger.debug(f"Response text: {response_text}")

    # Create TwiML response
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)

    return Response(content=str(twiml_response), media_type="application/xml")
