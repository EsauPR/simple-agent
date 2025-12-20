from typing import Optional, Type, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool, ToolRuntime
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


# ============ Input Schemas ============

class SearchCarsInput(BaseModel):
    """Input para buscar autos en el catálogo"""
    make: Optional[str] = Field(None, description="Marca del auto (ej: Toyota, Honda, BMW)")
    model: Optional[str] = Field(None, description="Modelo del auto (ej: Corolla, Civic, X5)")
    min_year: Optional[int] = Field(None, description="Año mínimo del auto")
    max_year: Optional[int] = Field(None, description="Año máximo del auto")
    min_price: Optional[float] = Field(None, description="Precio mínimo en pesos")
    max_price: Optional[float] = Field(None, description="Precio máximo en pesos")
    limit: int = Field(5, description="Número máximo de resultados")


class CalculateFinancingInput(BaseModel):
    """Input para calcular financiamiento"""
    car_price: float = Field(..., description="Precio del auto en pesos")
    down_payment: float = Field(..., description="Enganche en pesos")
    stock_id: Optional[str] = Field(None, description="Stock ID del auto (opcional)")


class SearchKnowledgeBaseInput(BaseModel):
    """Input para buscar en la base de conocimiento"""
    query: str = Field(..., description="Pregunta o consulta sobre Kavak")


class GetCarDetailsInput(BaseModel):
    """Input para obtener detalles de un auto"""
    stock_id: Optional[str] = Field(None, description="Stock ID del auto")
    reference: Optional[str] = Field(None, description="Referencia contextual como 'ese auto', 'el anterior'")


# ============ Tools ============

def create_search_cars_tool(db: AsyncSession):
    """Crea la tool para buscar autos"""

    @tool
    async def search_cars(
        make: Optional[str] = None,
        model: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 5,
        runtime: ToolRuntime = None  # Hidden parameter, not shown to model
    ) -> str:
        """Busca autos en el catálogo de Kavak basado en preferencias del cliente.
        Usa esta herramienta cuando el usuario quiera recomendaciones de autos o busque un auto específico.
        Puedes filtrar por marca, modelo, año y precio.
        """
        from src.services.car_service import CarService
        from src.services.agent.memory_manager import memory_manager

        car_service = CarService(db)

        cars = await car_service.search_cars(
            make=make,
            model=model,
            min_year=min_year,
            max_year=max_year,
            min_price=Decimal(str(min_price)) if min_price else None,
            max_price=Decimal(str(max_price)) if max_price else None,
            limit=limit
        )

        if not cars:
            return "No encontré autos que coincidan con esas preferencias. Intenta con otros criterios."

        # Convertir DTOs a diccionarios para el memory_manager
        cars_dict = [car.model_dump() for car in cars]

        # Save in context for future references
        if runtime:
            # Get thread_id from config
            thread_id = runtime.config.get("configurable", {}).get("thread_id") if runtime.config else None
            if thread_id:
                memory_manager.update_context(thread_id, last_cars_recommended=cars_dict)
                # Also update agent state if available
                if hasattr(runtime, 'state') and runtime.state:
                    runtime.state["last_cars_recommended"] = cars_dict

        # Formatear resultados
        result_lines = ["Encontré los siguientes autos disponibles:\n"]
        for i, car in enumerate(cars, 1):
            result_lines.append(
                f"{i}. {car.make} {car.model} {car.year} "
                f"(Stock ID: {car.stock_id}, Precio: ${float(car.price):,.0f}, "
                f"KM: {car.km:,})"
            )

        return "\n".join(result_lines)

    return search_cars


def create_calculate_financing_tool():
    """Crea la tool para calcular financiamiento"""

    @tool
    def calculate_financing(
        car_price: float,
        down_payment: float,
        stock_id: Optional[str] = None
    ) -> str:
        """Calcula planes de financiamiento para un auto.
        Usa esta herramienta cuando el usuario pregunte por mensualidades, financiamiento, o pagos mensuales.
        Necesitas el precio del auto y el enganche. La tasa de interés es 10% anual fija.

        IMPORTANTE: Los plazos disponibles son SOLO 3, 4, 5 o 6 años. Esta herramienta calcula automáticamente
        todos los plazos válidos (3, 4, 5, 6 años) y muestra las opciones al usuario.

        Si el usuario menciona un plazo diferente a 3, 4, 5 o 6 años, NO uses esta herramienta.
        En su lugar, informa al usuario que solo se ofrecen plazos de 3, 4, 5 o 6 años y pídele que elija uno válido.
        """
        from src.services.financing_service import FinancingService

        financing_service = FinancingService()
        car_price_decimal = Decimal(str(car_price))
        down_payment_decimal = Decimal(str(down_payment))

        if down_payment_decimal >= car_price_decimal:
            return "No se pudieron calcular los planes de financiamiento. El enganche debe ser menor al precio del auto."

        financed_amount = car_price_decimal - down_payment_decimal
        plans = []

        # Calculate plans for all available terms (3, 4, 5, 6 years)
        for years in [3, 4, 5, 6]:
            try:
                plan = financing_service.calculate_financing_plan(
                    car_price=car_price_decimal,
                    down_payment=down_payment_decimal,
                    years=years
                )
                plans.append(plan)
            except ValueError:
                continue

        if not plans:
            return "No se pudieron calcular los planes de financiamiento. Verifica que el enganche sea menor al precio del auto."

        result_lines = [
            "Planes de financiamiento disponibles:",
            f"- Precio del auto: ${car_price:,.0f}",
            f"- Enganche: ${down_payment:,.0f}",
            f"- Monto a financiar: ${float(financed_amount):,.0f}",
            "- Tasa de interés: 10% anual",
            "\nOpciones de pago mensual (plazos disponibles: 3, 4, 5 o 6 años):"
        ]

        for plan in plans:
            result_lines.append(
                f"- {plan.months} meses ({plan.years} años): ${plan.monthly_payment:,.2f}/mes "
                f"(Total: ${plan.total_amount:,.2f})"
            )

        result_lines.append(
            "\nNota: Los plazos disponibles son únicamente 3, 4, 5 o 6 años. "
            "Si deseas calcular un plazo específico, por favor elige uno de estos plazos válidos."
        )

        return "\n".join(result_lines)

    return calculate_financing


def create_search_knowledge_base_tool(db: AsyncSession):
    """Crea la tool para buscar en la base de conocimiento"""

    @tool
    async def search_kavak_info(query: str) -> str:
        """Busca información sobre Kavak, sus servicios, ubicaciones, propuesta de valor, etc.
        Usa esta herramienta cuando el usuario pregunte sobre qué es Kavak, dónde están ubicados,
        qué servicios ofrecen, o cualquier información general sobre la empresa.
        """
        from src.services.embedding_service import EmbeddingService
        from src.config import settings

        embedding_service = EmbeddingService(db)

        try:
            similar_chunks = await embedding_service.search_similar(
                query,
                limit=settings.RAG_TOP_K
            )

            if not similar_chunks:
                return "No encontré información específica sobre eso en mi base de conocimiento."

            # Combinar contenido relevante
            context = "\n\n".join([chunk.content for chunk in similar_chunks])
            return f"Información encontrada sobre Kavak:\n\n{context}"

        except Exception:
            return "No pude buscar información en este momento. Por favor intenta de nuevo."

    return search_kavak_info


def create_get_car_details_tool(db: AsyncSession):
    """Crea la tool para obtener detalles de un auto"""

    @tool
    async def get_car_details(
        stock_id: Optional[str] = None,
        reference: Optional[str] = None,
        runtime: ToolRuntime = None  # Hidden parameter, not shown to model
    ) -> str:
        """Obtiene detalles completos de un auto específico.
        Usa esta herramienta cuando necesites información de un auto por su Stock ID,
        o cuando el usuario haga referencia a 'ese auto', 'el anterior', 'el primero', etc.
        """
        from src.services.car_service import CarService
        from src.services.agent.memory_manager import memory_manager

        car_service = CarService(db)
        car = None

        # If there's a contextual reference, search in agent state or context
        car_dict = None
        if reference and runtime:
            # First try from agent state
            if hasattr(runtime, 'state') and runtime.state:
                if runtime.state.get("selected_car"):
                    car_dict = runtime.state["selected_car"]
                elif runtime.state.get("last_cars_recommended"):
                    car_dict = runtime.state["last_cars_recommended"][0]

            # If not in state, search in additional context
            if not car_dict:
                thread_id = runtime.config.get("configurable", {}).get("thread_id") if runtime.config else None
                if thread_id:
                    context = memory_manager.get_context(thread_id)
                    if context:
                        ref_lower = reference.lower()
                        if any(r in ref_lower for r in ["ese auto", "el anterior", "ese", "el primero", "el que me dijiste"]):
                            if context.selected_car:
                                car_dict = context.selected_car
                            elif context.last_cars_recommended:
                                car_dict = context.last_cars_recommended[0]

        # If there's stock_id, search directly
        car = None
        if not car_dict and stock_id:
            from src.repositories.car_repository import CarRepository
            from src.schemas.car import CarResponse
            car_repo = CarRepository(db)
            car_model = await car_repo.get_by_stock_id(stock_id)
            if car_model:
                car = CarResponse.model_validate(car_model)

        # If we have a dictionary from context, convert it to DTO
        if car_dict and not car:
            from src.schemas.car import CarResponse
            car = CarResponse.model_validate(car_dict)

        if not car:
            return "No encontré el auto especificado. Por favor proporciona el Stock ID o busca autos primero."

        # Save as selected car (convert to dict for memory_manager)
        car_dict = car.model_dump()
        if runtime:
            thread_id = runtime.config.get("configurable", {}).get("thread_id") if runtime.config else None
            if thread_id:
                memory_manager.update_context(thread_id, selected_car=car_dict)
            # Also update agent state if available
            if hasattr(runtime, 'state') and runtime.state:
                runtime.state["selected_car"] = car_dict

        return (
            f"Detalles del auto:\n"
            f"- Marca: {car.make}\n"
            f"- Modelo: {car.model}\n"
            f"- Año: {car.year}\n"
            f"- Precio: ${float(car.price):,.0f}\n"
            f"- Kilometraje: {car.km:,} km\n"
            f"- Versión: {car.version or 'N/A'}\n"
            f"- Stock ID: {car.stock_id}\n"
            f"- Bluetooth: {'Sí' if car.bluetooth else 'No'}\n"
            f"- CarPlay: {'Sí' if car.car_play else 'No'}"
        )

    return get_car_details


def create_tools(db: AsyncSession, phone_number: Optional[str] = None) -> List[BaseTool]:
    """Crea las herramientas para el agente"""
    return [
        create_search_cars_tool(db),
        create_calculate_financing_tool(),
        create_search_knowledge_base_tool(db),
        create_get_car_details_tool(db),
    ]
