import logging

from sqlalchemy.ext.asyncio import AsyncSession
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from src.config import settings
from src.services.agent.memory_manager import memory_manager, CustomAgentState
from src.services.agent.langchain_tools import create_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un agente comercial de Kavak, la empresa líder en compra y venta de autos seminuevos en México.

Tu objetivo es ayudar a los clientes de forma amigable y profesional. Puedes:

1. **Información sobre Kavak**: Responder preguntas sobre la empresa, servicios, ubicaciones y propuesta de valor. Usa la herramienta 'search_kavak_info' para buscar información.

2. **Recomendaciones de autos**: Ayudar a encontrar el auto ideal según las preferencias del cliente (marca, modelo, año, presupuesto). Usa la herramienta 'search_cars' para buscar en el catálogo.

3. **Planes de financiamiento**: Calcular mensualidades y planes de pago. Usa la herramienta 'calculate_financing'. La tasa de interés es del 10% anual. IMPORTANTE: Los plazos disponibles son SOLO 3, 4, 5 o 6 años. Si el usuario menciona un plazo diferente, debes informarle que solo se pueden ofrecer plazos de 3, 4, 5 o 6 años y pedirle que elija uno de estos plazos válidos.

4. **Detalles de autos**: Obtener información detallada de un auto específico. Usa la herramienta 'get_car_details'.

Instrucciones importantes:
- **LÍMITE DE CARACTERES CRÍTICO**: Tus respuestas NO deben superar 1000 caracteres. Las respuestas se envían por WhatsApp y deben ser concisas. Resume la información de manera clara y directa. Si tienes mucha información, prioriza lo más importante y ofrece continuar en otro mensaje si es necesario.
- Siempre mantén un tono profesional pero amigable
- Si el usuario menciona "ese auto", "el anterior" o referencias similares, usa la herramienta 'get_car_details' con la referencia
- Para calcular financiamiento, necesitas el precio del auto y el enganche. Si no tienes el precio, primero busca el auto
- Si el usuario pregunta por un plazo de financiamiento, VALIDA que sea 3, 4, 5 o 6 años. Si menciona otro plazo (ej: 2 años, 7 años, 24 meses, etc.), explícale amablemente que solo se ofrecen plazos de 3, 4, 5 o 6 años y pídele que elija uno de estos
- Si no tienes suficiente información para ayudar, pregunta amablemente al usuario
- Responde siempre en español
- Sé MUY conciso pero informativo - prioriza la información esencial
- Si el usuario pregunta algo fuera de tu alcance (compra de autos nuevos, servicios de taller, etc.), indica amablemente que solo puedes ayudar con autos seminuevos de Kavak
- Usa viñetas y listas cortas para organizar información de manera compacta
"""


class ChatService:
    """Servicio de chat usando LangChain Agent con checkpointer"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        self.checkpointer = memory_manager.get_checkpointer()

        # Create tools (without initial phone_number, will be passed in config)
        self.tools = create_tools(self.db, None)

        # Create agent once with checkpointer
        self.agent = create_agent(
            self.llm,
            tools=self.tools,
            system_prompt=SYSTEM_PROMPT,
            state_schema=CustomAgentState,
            checkpointer=self.checkpointer
        )

    async def process_message(
        self,
        phone_number: str,
        user_message: str
    ) -> str:
        """Process a user message and generate response using the agent"""
        logger.debug(f"Processing message for phone number: {phone_number}")
        logger.debug(f"User message: {user_message}")
        initial_state = {
            "messages": [{"role": "user", "content": user_message}]
        }

        # Configure thread_id to maintain conversation
        # The checkpointer will automatically restore the previous state including
        # last_cars_recommended and selected_car from previous interactions
        config: RunnableConfig = {
            "configurable": {"thread_id": phone_number}
        }

        try:
            # Execute the agent
            result = await self.agent.ainvoke(initial_state, config)

            logger.debug(f"Agent result: {result}")

            # Get the last response from the agent
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = "Lo siento, no pude procesar tu mensaje. ¿Podrías reformularlo?"

            # Ensure response doesn't exceed configured limit to keep it within WhatsApp limits
            if len(response) > settings.MAX_RESPONSE_LENGTH:
                logger.warning(f"Response exceeded {settings.MAX_RESPONSE_LENGTH} characters ({len(response)}), truncating...")
                # Truncate at the last complete sentence before the limit
                truncated = response[:settings.MAX_RESPONSE_LENGTH]
                last_period = truncated.rfind('.')
                last_newline = truncated.rfind('\n')
                # Use the last complete sentence or line, whichever is closer to the limit
                cut_point = max(last_period, last_newline)
                if cut_point > settings.MAX_RESPONSE_LENGTH * 0.8:  # Only if we can keep at least 80% of the message
                    response = truncated[:cut_point + 1]
                else:
                    response = truncated

            return response

        except Exception as e:
            # In case of error, try to give a friendly response
            logger.error(f"Error processing message: {e}")
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?"
