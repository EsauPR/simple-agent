from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.services.agent.chat_service import ChatService
from src.services.agent.memory_manager import memory_manager
from src.schemas.chat import ChatMessageRequest, ChatMessageResponse
from src.config import settings

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

        if not validator.validate(url, params, signature):
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

    # Create TwiML response
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)

    return Response(content=str(twiml_response), media_type="application/xml")


@router.get("/sessions/{phone_number}")
async def get_session(phone_number: str):
    """Get the memory/session of a user (debug/admin)"""
    memory_dict = memory_manager.get_memory_as_dict(phone_number)
    if not memory_dict:
        raise HTTPException(status_code=404, detail="Session not found")
    return memory_dict


@router.delete("/sessions/{phone_number}")
async def clear_session(phone_number: str):
    """Clear the memory/session of a user"""
    memory_manager.clear_memory(phone_number)
    return {"message": "Session cleared"}
