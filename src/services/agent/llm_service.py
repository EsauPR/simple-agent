from typing import List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings


class LLMService:
    """Servicio de LLM usando LangChain con OpenAI"""

    def __init__(self):
        self.chat_model = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )

    def get_chat_model(self, temperature: float = 0.7) -> ChatOpenAI:
        """Retorna el modelo de chat con la temperatura especificada"""
        if temperature != 0.7:
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
        return self.chat_model

    async def generate_embedding(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        return await self.embeddings.aembed_query(text)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos"""
        return await self.embeddings.aembed_documents(texts)

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7
    ) -> str:
        """Genera una respuesta de chat simple"""
        model = self.get_chat_model(temperature)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        response = await model.ainvoke(messages)
        return response.content


# Instancia global del servicio
llm_service = LLMService()
