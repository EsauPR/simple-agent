"""Tests for LLMService"""
import pytest

from src.services.agent.llm_service import LLMService


@pytest.mark.asyncio
class TestLLMService:
    """Tests for LLMService"""

    async def test_generate_embedding(self, mock_openai_client):
        """Test generating an embedding"""
        service = LLMService()

        embedding = await service.generate_embedding("Test text")

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        # Verify mock was called
        service.embeddings.aembed_query.assert_called_once_with("Test text")

    async def test_generate_embeddings(self, mock_openai_client):
        """Test generating multiple embeddings"""
        service = LLMService()

        texts = ["Text 1", "Text 2"]
        embeddings = await service.generate_embeddings(texts)

        assert embeddings is not None
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        # Verify mock was called
        service.embeddings.aembed_documents.assert_called_once_with(texts)

    async def test_chat(self, mock_openai_client):
        """Test chat functionality"""
        service = LLMService()

        system_prompt = "You are a helpful assistant"
        user_message = "Hello"

        response = await service.chat(system_prompt, user_message)

        assert response is not None
        assert isinstance(response, str)
        # Verify the model was invoked
        assert service.chat_model.ainvoke.called

    async def test_chat_with_temperature(self, mock_openai_client):
        """Test chat with custom temperature"""
        service = LLMService()

        system_prompt = "You are a helpful assistant"
        user_message = "Hello"
        temperature = 0.5

        response = await service.chat(system_prompt, user_message, temperature=temperature)

        assert response is not None
        # When temperature is different, a new model should be created
        # The default model should still exist
        assert service.chat_model is not None

    async def test_get_chat_model_default(self):
        """Test getting default chat model"""
        service = LLMService()

        model = service.get_chat_model()

        assert model is not None
        assert model == service.chat_model

    async def test_embeddings_model_initialization(self):
        """Test that embeddings model is initialized"""
        service = LLMService()

        assert service.embeddings is not None

    async def test_chat_model_initialization(self):
        """Test that chat model is initialized"""
        service = LLMService()

        assert service.chat_model is not None
