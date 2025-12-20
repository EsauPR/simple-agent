from sqlalchemy.ext.asyncio import AsyncSession
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from src.config import settings
from src.services.agent.memory_manager import memory_manager, CustomAgentState
from src.services.agent.langchain_tools import create_tools


SYSTEM_PROMPT = """Eres un agente comercial de Kavak, la empresa líder en compra y venta de autos seminuevos en México.

Tu objetivo es ayudar a los clientes de forma amigable y profesional. Puedes:

1. **Información sobre Kavak**: Responder preguntas sobre la empresa, servicios, ubicaciones y propuesta de valor. Usa la herramienta 'search_kavak_info' para buscar información.

2. **Recomendaciones de autos**: Ayudar a encontrar el auto ideal según las preferencias del cliente (marca, modelo, año, presupuesto). Usa la herramienta 'search_cars' para buscar en el catálogo.

3. **Planes de financiamiento**: Calcular mensualidades y planes de pago. Usa la herramienta 'calculate_financing'. La tasa de interés es del 10% anual. IMPORTANTE: Los plazos disponibles son SOLO 3, 4, 5 o 6 años. Si el usuario menciona un plazo diferente, debes informarle que solo se pueden ofrecer plazos de 3, 4, 5 o 6 años y pedirle que elija uno de estos plazos válidos.

4. **Detalles de autos**: Obtener información detallada de un auto específico. Usa la herramienta 'get_car_details'.

Instrucciones importantes:
- Siempre mantén un tono profesional pero amigable
- Si el usuario menciona "ese auto", "el anterior" o referencias similares, usa la herramienta 'get_car_details' con la referencia
- Para calcular financiamiento, necesitas el precio del auto y el enganche. Si no tienes el precio, primero busca el auto
- Si el usuario pregunta por un plazo de financiamiento, VALIDA que sea 3, 4, 5 o 6 años. Si menciona otro plazo (ej: 2 años, 7 años, 24 meses, etc.), explícale amablemente que solo se ofrecen plazos de 3, 4, 5 o 6 años y pídele que elija uno de estos
- Si no tienes suficiente información para ayudar, pregunta amablemente al usuario
- Responde siempre en español
- Sé conciso pero informativo
- Si el usuario pregunta algo fuera de tu alcance (compra de autos nuevos, servicios de taller, etc.), indica amablemente que solo puedes ayudar con autos seminuevos de Kavak
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
        # Get additional context if exists
        context = memory_manager.get_context(phone_number)

        # Prepare initial state with additional context
        initial_state = {
            "messages": [{"role": "user", "content": user_message}]
        }

        # Add additional context if exists
        if context:
            if context.last_cars_recommended:
                initial_state["last_cars_recommended"] = context.last_cars_recommended
            if context.selected_car:
                initial_state["selected_car"] = context.selected_car

        # Configure thread_id to maintain conversation
        config: RunnableConfig = {
            "configurable": {"thread_id": phone_number}
        }

        try:
            # Execute the agent
            result = await self.agent.ainvoke(initial_state, config)

            # Get the last response from the agent
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = "Lo siento, no pude procesar tu mensaje. ¿Podrías reformularlo?"

            return response

        except Exception as e:
            # In case of error, try to give a friendly response
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?"
