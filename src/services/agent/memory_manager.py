import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import AgentState
from src.config import settings


@dataclass
class SessionContext:
    """Additional session context (recommended cars, selected car)"""
    last_cars_recommended: List[Dict[str, Any]] = field(default_factory=list)
    selected_car: Optional[Dict[str, Any]] = None
    last_activity: datetime = field(default_factory=datetime.now)


class CustomAgentState(AgentState):
    """Custom agent state with additional context"""
    last_cars_recommended: List[Dict[str, Any]] = []
    selected_car: Optional[Dict[str, Any]] = None


class MemoryManager:
    """Manages checkpointer instances and additional context by phone number"""

    def __init__(self):
        self.checkpointer = InMemorySaver()
        self._contexts: Dict[str, SessionContext] = {}
        self._lock = asyncio.Lock()
        self._ttl_hours = settings.SESSION_TTL_HOURS

    def get_checkpointer(self):
        """Returns the checkpointer to use with the agent"""
        return self.checkpointer

    def get_context(self, phone_number: str) -> Optional[SessionContext]:
        """Get additional session context"""
        context = self._contexts.get(phone_number)
        if context:
            context.last_activity = datetime.now()
        return context

    def update_context(
        self,
        phone_number: str,
        last_cars_recommended: Optional[List[Dict[str, Any]]] = None,
        selected_car: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update additional session context"""
        if phone_number not in self._contexts:
            self._contexts[phone_number] = SessionContext()

        context = self._contexts[phone_number]

        if last_cars_recommended is not None:
            context.last_cars_recommended = last_cars_recommended

        if selected_car is not None:
            context.selected_car = selected_car

        context.last_activity = datetime.now()

    def clear_memory(self, phone_number: str) -> None:
        """Clear user memory"""
        # Clear additional context
        if phone_number in self._contexts:
            del self._contexts[phone_number]
        # The checkpointer maintains state, but we can clear it if needed
        # For now, let TTL handle it

    async def cleanup_inactive_memories(self) -> int:
        """Remove inactive memories (older than TTL)"""
        now = datetime.now()
        threshold = now - timedelta(hours=self._ttl_hours)

        async with self._lock:
            to_delete = [
                phone for phone, context in self._contexts.items()
                if context.last_activity < threshold
            ]

            for phone in to_delete:
                self.clear_memory(phone)

            return len(to_delete)

    def get_memory_as_dict(self, phone_number: str) -> Optional[dict]:
        """Get memory as dictionary (for API/debug)"""
        context = self._contexts.get(phone_number)

        # Try to get messages from checkpointer
        # Note: This requires access to saved state, which may not be directly available
        # For now, return additional context
        return {
            "phone_number": phone_number,
            "context": {
                "last_cars_recommended": context.last_cars_recommended if context else [],
                "selected_car": context.selected_car if context else None
            },
            "last_activity": context.last_activity.isoformat() if context else None
        }


# Global memory manager instance
memory_manager = MemoryManager()
