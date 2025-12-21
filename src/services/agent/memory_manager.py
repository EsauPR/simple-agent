from typing import Dict, Any, List, Optional
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import AgentState


class CustomAgentState(AgentState):
    """Custom agent state with additional context for cars"""
    last_cars_recommended: List[Dict[str, Any]] = []
    selected_car: Optional[Dict[str, Any]] = None


class MemoryManager:
    """Manages checkpointer instance for agent state persistence"""

    def __init__(self):
        self.checkpointer = InMemorySaver()

    def get_checkpointer(self):
        """Returns the checkpointer to use with the agent"""
        return self.checkpointer


# Global memory manager instance
memory_manager = MemoryManager()
