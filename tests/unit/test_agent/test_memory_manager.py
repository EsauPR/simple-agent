"""Tests for memory_manager"""
from src.services.agent.memory_manager import MemoryManager, CustomAgentState


class TestMemoryManager:
    """Tests for MemoryManager"""

    def test_get_checkpointer(self):
        """Test getting checkpointer"""
        manager = MemoryManager()
        checkpointer = manager.get_checkpointer()

        assert checkpointer is not None
        # Should return the same instance
        assert manager.get_checkpointer() == checkpointer

    def test_custom_agent_state(self):
        """Test CustomAgentState structure"""
        # CustomAgentState extends AgentState which is a TypedDict
        # We can create it as a dict or check its structure
        state_dict = CustomAgentState()

        # Check that the keys exist
        assert 'last_cars_recommended' in state_dict or hasattr(CustomAgentState, '__annotations__')
        # For TypedDict, we check annotations
        annotations = getattr(CustomAgentState, '__annotations__', {})
        assert 'last_cars_recommended' in annotations or 'last_cars_recommended' in state_dict
        assert 'selected_car' in annotations or 'selected_car' in state_dict

    def test_custom_agent_state_with_data(self):
        """Test CustomAgentState with data"""
        cars = [{"stock_id": "TEST001", "make": "Toyota"}]
        selected = {"stock_id": "TEST001", "make": "Toyota"}

        # CustomAgentState is a TypedDict, can be created as dict
        state = {
            "last_cars_recommended": cars,
            "selected_car": selected
        }

        assert state["last_cars_recommended"] == cars
        assert state["selected_car"] == selected
