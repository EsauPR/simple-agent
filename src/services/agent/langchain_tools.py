import logging
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool, ToolRuntime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.car_service import CarService
from src.services.agent.memory_manager import memory_manager
from src.services.embedding_service import EmbeddingService
from src.services.financing_service import FinancingService
from src.repositories.car_repository import CarRepository
from src.schemas.car import CarResponse
from src.config import settings

logger = logging.getLogger(__name__)

# Input Schemas

class SearchCarsInput(BaseModel):
    """Input to search cars in the catalog"""
    make: Optional[str] = Field(None, description="Make of the car (e.g: Toyota, Honda, BMW)")
    model: Optional[str] = Field(None, description="Model of the car (e.g: Corolla, Civic, X5)")
    min_year: Optional[int] = Field(None, description="Minimum year of the car")
    max_year: Optional[int] = Field(None, description="Maximum year of the car")
    min_price: Optional[float] = Field(None, description="Minimum price in pesos")
    max_price: Optional[float] = Field(None, description="Maximum price in pesos")
    limit: int = Field(5, description="Maximum number of results")


class CalculateFinancingInput(BaseModel):
    """Input to calculate financing"""
    car_price: float = Field(..., description="Price of the car in pesos")
    down_payment: float = Field(..., description="Down payment in pesos")
    stock_id: Optional[str] = Field(None, description="Stock ID of the car (optional)")


class SearchKnowledgeBaseInput(BaseModel):
    """Input to search in the knowledge base"""
    query: str = Field(..., description="Question or query about Kavak")


class GetCarDetailsInput(BaseModel):
    """Input to get details of a car"""
    stock_id: Optional[str] = Field(None, description="Stock ID of the car")
    reference: Optional[str] = Field(None, description="Contextual reference like 'that car', 'the previous one'")


# Tools

def create_search_cars_tool(db: AsyncSession):
    """Create the tool to search cars"""

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
        """Search cars in the Kavak catalog based on customer preferences.
        Use this tool when the user wants to recommend cars or search for a specific car.
        You can filter by make, model, year and price.
        """
        logger.info(
            f"Executing tool search_cars - make={make}, model={model}, min_year={min_year}, "
            f"max_year={max_year}, min_price={min_price}, max_price={max_price}, limit={limit}"
        )
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
            logger.debug("Cars not found")
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
    """Create the tool to calculate the financing plan"""

    @tool
    def calculate_financing(
        car_price: float,
        down_payment: float,
        stock_id: Optional[str] = None
    ) -> str:
        """Calculate financing plans for a car.
        Use this tool when the user asks for monthly payments, financing, or monthly payments.
        You need the price of the car and the down payment. The interest rate is 10% annual fixed.

        IMPORTANT: The available terms are ONLY 3, 4, 5 or 6 years. This tool automatically
        calculates all valid terms (3, 4, 5, 6 years) and shows the options to the user.

        If the user mentions a term different from 3, 4, 5 or 6 years, DO NOT use this tool.
        Instead, inform the user that only terms of 3, 4, 5 or 6 years are available and ask them to choose one valid.
        """
        logger.info(f"Executing tool calculate_financing - car_price={car_price}, down_payment={down_payment}, stock_id={stock_id}")

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
    """Create the tool to search in the knowledge base"""

    @tool
    async def search_kavak_info(query: str) -> str:
        """Search information about Kavak, its services, locations, value proposition, etc.
        Use this tool when the user asks about what Kavak is, where it is located,
        what services it offers, or any general information about Kavak.
        """
        logger.info(f"Executing tool search_kavak_info - query={query}")
        embedding_service = EmbeddingService(db)

        try:
            similar_chunks = await embedding_service.search_similar(
                query,
                limit=settings.RAG_TOP_K
            )

            if not similar_chunks:
                logger.debug("No similar chunks found")
                return "No encontré información específica sobre eso en mi base de conocimiento."

            # Combinar contenido relevante
            context = "\n\n".join([chunk.content for chunk in similar_chunks])
            logger.debug(f"Context: {context}")
            return f"Información encontrada sobre Kavak:\n\n{context}"

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return "No pude buscar información en este momento. Por favor intenta de nuevo."

    return search_kavak_info


def create_get_car_details_tool(db: AsyncSession):
    """Create the tool to obtain the car details"""

    @tool
    async def get_car_details(
        stock_id: Optional[str] = None,
        reference: Optional[str] = None,
        runtime: ToolRuntime = None  # Hidden parameter, not shown to model
    ) -> str:
        """Get the complete details of a specific car.
        Use this tool when you need information about a car by its Stock ID,
        or when the user makes reference to 'that car', 'the previous one', 'the first one', etc.
        """
        logger.info(f"Executing tool get_car_details - stock_id={stock_id}, reference={reference}")
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
            car_repo = CarRepository(db)
            car_model = await car_repo.get_by_stock_id(stock_id)
            if car_model:
                car = CarResponse.model_validate(car_model)

        # If we have a dictionary from context, convert it to DTO
        if car_dict and not car:
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
    """Create the tools for the agent"""
    return [
        create_search_cars_tool(db),
        create_calculate_financing_tool(),
        create_search_knowledge_base_tool(db),
        create_get_car_details_tool(db),
    ]
