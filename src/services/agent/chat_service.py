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

3. **Planes de financiamiento**: Calcular mensualidades y planes de pago. Usa la herramienta 'calculate_financing'. La tasa de interés es del 10% anual y los plazos disponibles son de 3 a 6 años.

4. **Detalles de autos**: Obtener información detallada de un auto específico. Usa la herramienta 'get_car_details'.

Instrucciones importantes:
- Siempre mantén un tono profesional pero amigable
- Si el usuario menciona "ese auto", "el anterior" o referencias similares, usa la herramienta 'get_car_details' con la referencia
- Para calcular financiamiento, necesitas el precio del auto y el enganche. Si no tienes el precio, primero busca el auto
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

        # Crear herramientas (sin phone_number inicial, se pasará en el config)
        self.tools = create_tools(self.db, None)

        # Crear el agente una sola vez con checkpointer
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
        """Procesa un mensaje del usuario y genera respuesta usando el agente"""
        # Obtener contexto adicional si existe
        context = memory_manager.get_context(phone_number)

        # Preparar el estado inicial con contexto adicional
        initial_state = {
            "messages": [{"role": "user", "content": user_message}]
        }

        # Agregar contexto adicional si existe
        if context:
            if context.last_cars_recommended:
                initial_state["last_cars_recommended"] = context.last_cars_recommended
            if context.selected_car:
                initial_state["selected_car"] = context.selected_car

        # Configurar thread_id para mantener la conversación
        config: RunnableConfig = {
            "configurable": {"thread_id": phone_number}
        }

        try:
            # Ejecutar el agente
            result = await self.agent.ainvoke(initial_state, config)

            # Obtener la última respuesta del agente
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = "Lo siento, no pude procesar tu mensaje. ¿Podrías reformularlo?"

            return response

        except Exception as e:
            # En caso de error, intentar dar una respuesta amigable
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?"
