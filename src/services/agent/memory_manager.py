import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import AgentState
from src.config import settings


@dataclass
class SessionContext:
    """Contexto adicional de la sesión (autos recomendados, auto seleccionado)"""
    last_cars_recommended: List[Dict[str, Any]] = field(default_factory=list)
    selected_car: Optional[Dict[str, Any]] = None
    last_activity: datetime = field(default_factory=datetime.now)


class CustomAgentState(AgentState):
    """Estado personalizado del agente con contexto adicional"""
    last_cars_recommended: List[Dict[str, Any]] = []
    selected_car: Optional[Dict[str, Any]] = None


class MemoryManager:
    """Gestiona instancias de checkpointer y contexto adicional por número de teléfono"""

    def __init__(self):
        self.checkpointer = InMemorySaver()
        self._contexts: Dict[str, SessionContext] = {}
        self._lock = asyncio.Lock()
        self._ttl_hours = settings.SESSION_TTL_HOURS

    def get_checkpointer(self):
        """Retorna el checkpointer para usar con el agente"""
        return self.checkpointer

    def get_context(self, phone_number: str) -> Optional[SessionContext]:
        """Obtiene el contexto adicional de la sesión"""
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
        """Actualiza el contexto adicional de la sesión"""
        if phone_number not in self._contexts:
            self._contexts[phone_number] = SessionContext()

        context = self._contexts[phone_number]

        if last_cars_recommended is not None:
            context.last_cars_recommended = last_cars_recommended

        if selected_car is not None:
            context.selected_car = selected_car

        context.last_activity = datetime.now()

    def clear_memory(self, phone_number: str) -> None:
        """Limpia la memoria de un usuario"""
        # Limpiar contexto adicional
        if phone_number in self._contexts:
            del self._contexts[phone_number]
        # El checkpointer mantiene el estado, pero podemos limpiarlo si es necesario
        # Por ahora, dejamos que el TTL lo maneje

    async def cleanup_inactive_memories(self) -> int:
        """Elimina memorias inactivas (más antiguas que TTL)"""
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
        """Obtiene la memoria como diccionario (para API/debug)"""
        from langchain_core.messages import HumanMessage

        context = self._contexts.get(phone_number)

        # Intentar obtener mensajes del checkpointer
        # Nota: Esto requiere acceso al estado guardado, que puede no estar disponible directamente
        # Por ahora, retornamos el contexto adicional
        return {
            "phone_number": phone_number,
            "context": {
                "last_cars_recommended": context.last_cars_recommended if context else [],
                "selected_car": context.selected_car if context else None
            },
            "last_activity": context.last_activity.isoformat() if context else None
        }


# Instancia global del gestor de memoria
memory_manager = MemoryManager()
