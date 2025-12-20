from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class SessionContext(BaseModel):
    last_intent: Optional[str] = None
    last_cars_recommended: List[Dict[str, Any]] = []
    selected_car: Optional[Dict[str, Any]] = None
    pending_info: Dict[str, Any] = {}
    conversation_state: Optional[str] = None


class Session(BaseModel):
    phone_number: str
    messages: List[Message] = []
    context: SessionContext = SessionContext()
    created_at: datetime
    last_activity: datetime


class ChatMessageRequest(BaseModel):
    message: str
    phone_number: str


class ChatMessageResponse(BaseModel):
    response: str
    phone_number: str
