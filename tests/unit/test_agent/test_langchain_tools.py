"""Tests for langchain_tools"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

from src.services.agent.langchain_tools import (
    create_search_cars_tool,
    create_calculate_financing_tool,
    create_search_knowledge_base_tool,
    create_get_car_details_tool,
    create_tools,
)
from src.schemas.car import CarResponse
from src.schemas.embedding import EmbeddingSearchResult
from src.schemas.financing import FinancingPlan


class TestLangchainTools:
    """Tests for LangChain tools"""

    async def test_search_cars_tool(self, test_db, mock_runtime):
        """Test search_cars tool"""
        tool = create_search_cars_tool(test_db)

        # Mock CarService
        mock_car = MagicMock(spec=CarResponse)
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "TOOL001"
        mock_car.km = 50000
        mock_car.model_dump = MagicMock(return_value={
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "price": "200000",
            "stock_id": "TOOL001",
            "km": 50000
        })

        with patch('src.services.agent.langchain_tools.CarService') as mock_car_service_class:
            mock_car_service = MagicMock()
            mock_car_service.search_cars = AsyncMock(return_value=[mock_car])
            mock_car_service_class.return_value = mock_car_service

            # Use ainvoke directly - runtime is optional and hidden from the model
            # We'll verify the behavior without runtime since it's not part of the tool's public API
            result = await tool.ainvoke({
                "make": "Toyota",
                "limit": 5
            })

            # Verify service was called correctly
            mock_car_service.search_cars.assert_called_once()
            call_kwargs = mock_car_service.search_cars.call_args[1]
            assert call_kwargs["make"] == "Toyota"
            assert call_kwargs["limit"] == 5

            # Verify result contains expected information
            assert "Toyota" in result
            assert "Corolla" in result
            assert "TOOL001" in result

    async def test_search_cars_tool_no_results(self, test_db, mock_runtime):
        """Test search_cars tool with no results"""
        tool = create_search_cars_tool(test_db)

        with patch('src.services.agent.langchain_tools.CarService') as mock_car_service_class:
            mock_car_service = MagicMock()
            mock_car_service.search_cars = AsyncMock(return_value=[])
            mock_car_service_class.return_value = mock_car_service

            # Use ainvoke directly - runtime is optional
            result = await tool.ainvoke({
                "make": "Ferrari",
                "limit": 5
            })

            assert "No encontré" in result or "no coincidan" in result.lower()

    def test_calculate_financing_tool(self):
        """Test calculate_financing tool"""
        tool = create_calculate_financing_tool()

        # Mock FinancingService
        mock_plans = {
            3: FinancingPlan(
                years=3,
                months=36,
                monthly_payment=Decimal("5000.00"),
                total_amount=Decimal("180000.00"),
                interest_amount=Decimal("20000.00")
            ),
            4: FinancingPlan(
                years=4,
                months=48,
                monthly_payment=Decimal("4000.00"),
                total_amount=Decimal("192000.00"),
                interest_amount=Decimal("32000.00")
            ),
            5: FinancingPlan(
                years=5,
                months=60,
                monthly_payment=Decimal("3500.00"),
                total_amount=Decimal("210000.00"),
                interest_amount=Decimal("50000.00")
            ),
            6: FinancingPlan(
                years=6,
                months=72,
                monthly_payment=Decimal("3000.00"),
                total_amount=Decimal("216000.00"),
                interest_amount=Decimal("56000.00")
            ),
        }

        with patch('src.services.agent.langchain_tools.FinancingService') as mock_financing_service_class:
            mock_financing_service = MagicMock()
            # Mock calculate_financing_plan to return plans for each year
            def mock_calculate(car_price, down_payment, years):
                return mock_plans[years]

            mock_financing_service.calculate_financing_plan = MagicMock(side_effect=mock_calculate)
            mock_financing_service_class.return_value = mock_financing_service

            result = tool.invoke({
                "car_price": 200000.0,
                "down_payment": 40000.0,
            })

            # Verify service was called for each year
            assert mock_financing_service.calculate_financing_plan.call_count == 4

            # Verify result contains expected information
            assert "Planes de financiamiento" in result
            assert "3 años" in result or "36 meses" in result
            assert "4 años" in result or "48 meses" in result
            assert "5 años" in result or "60 meses" in result
            assert "6 años" in result or "72 meses" in result

    def test_calculate_financing_tool_invalid_down_payment(self):
        """Test calculate_financing with invalid down payment"""
        tool = create_calculate_financing_tool()

        result = tool.invoke({
            "car_price": 200000.0,
            "down_payment": 250000.0,  # Higher than price
        })

        assert "No se pudieron calcular" in result or "enganche" in result.lower()

    async def test_search_kavak_info_tool(self, test_db):
        """Test search_kavak_info tool"""
        tool = create_search_knowledge_base_tool(test_db)

        # Mock EmbeddingService
        mock_results = [
            EmbeddingSearchResult(
                id=uuid4(),
                content="Kavak es una empresa líder en compra y venta de autos seminuevos en México.",
                source_url="https://kavak.com",
                metadata=None
            )
        ]

        with patch('src.services.agent.langchain_tools.EmbeddingService') as mock_embedding_service_class, \
             patch('src.services.agent.langchain_tools.settings.RAG_TOP_K', 5):
            mock_embedding_service = MagicMock()
            mock_embedding_service.search_similar = AsyncMock(return_value=mock_results)
            mock_embedding_service_class.return_value = mock_embedding_service

            result = await tool.ainvoke({"query": "empresa autos"})

            # Verify service was called correctly
            mock_embedding_service.search_similar.assert_called_once_with(
                "empresa autos",
                limit=5  # Uses settings.RAG_TOP_K
            )

            # Verify result contains expected information
            assert "Kavak" in result or "empresa" in result

    async def test_search_kavak_info_tool_no_results(self, test_db):
        """Test search_kavak_info tool with no results"""
        tool = create_search_knowledge_base_tool(test_db)

        with patch('src.services.agent.langchain_tools.EmbeddingService') as mock_embedding_service_class:
            mock_embedding_service = MagicMock()
            mock_embedding_service.search_similar = AsyncMock(return_value=[])
            mock_embedding_service_class.return_value = mock_embedding_service

            result = await tool.ainvoke({"query": "test query"})

            assert "No encontré" in result or "no pude buscar" in result.lower()

    async def test_get_car_details_tool_by_stock_id(self, test_db, mock_runtime):
        """Test get_car_details tool by stock_id"""
        tool = create_get_car_details_tool(test_db)

        # Mock CarRepository
        from src.database.models import Car
        mock_car_model = MagicMock(spec=Car)
        mock_car_model.id = uuid4()
        mock_car_model.make = "Toyota"
        mock_car_model.model = "Corolla"
        mock_car_model.year = 2020
        mock_car_model.price = Decimal("200000")
        mock_car_model.stock_id = "DETAILS001"
        mock_car_model.km = 50000
        mock_car_model.version = "XEI"
        mock_car_model.bluetooth = True
        mock_car_model.car_play = False
        mock_car_model.length = Decimal("4.63")
        mock_car_model.width = Decimal("1.78")
        mock_car_model.height = Decimal("1.45")
        mock_car_model.created_at = datetime.now(timezone.utc)
        mock_car_model.updated_at = datetime.now(timezone.utc)

        with patch('src.services.agent.langchain_tools.CarRepository') as mock_car_repo_class:
            mock_car_repo = MagicMock()
            mock_car_repo.get_by_stock_id = AsyncMock(return_value=mock_car_model)
            mock_car_repo_class.return_value = mock_car_repo

            # Use ainvoke directly - runtime is optional
            result = await tool.ainvoke({
                "stock_id": "DETAILS001"
            })

            # Verify repository was called correctly
            mock_car_repo.get_by_stock_id.assert_called_once_with("DETAILS001")

            # Verify result contains expected information
            assert "Toyota" in result
            assert "Corolla" in result
            assert "2020" in result
            assert "DETAILS001" in result

    async def test_get_car_details_tool_by_reference(self, test_db, mock_runtime):
        """Test get_car_details tool by contextual reference

        Note: This test verifies that without runtime (which is provided by the agent),
        the tool cannot access contextual references. In a real scenario, the agent
        would provide the runtime with the state.
        """
        tool = create_get_car_details_tool(test_db)

        # Use ainvoke without runtime - this simulates the tool being called
        # without contextual state (runtime is provided by the agent framework)
        result = await tool.ainvoke({
            "reference": "ese auto"
        })

        # Without runtime, the tool should indicate it can't find the car
        # since it can't access the agent state
        assert "No encontré" in result or "especificado" in result.lower()

    async def test_get_car_details_tool_not_found(self, test_db, mock_runtime):
        """Test get_car_details tool with car not found"""
        tool = create_get_car_details_tool(test_db)

        with patch('src.services.agent.langchain_tools.CarRepository') as mock_car_repo_class:
            mock_car_repo = MagicMock()
            mock_car_repo.get_by_stock_id = AsyncMock(return_value=None)
            mock_car_repo_class.return_value = mock_car_repo

            # Use ainvoke directly - runtime is optional
            result = await tool.ainvoke({
                "stock_id": "NONEXISTENT"
            })

            assert "No encontré" in result or "especificado" in result.lower()

    @pytest.mark.asyncio
    async def test_create_tools(self, test_db):
        """Test create_tools function"""
        tools = create_tools(test_db)

        assert len(tools) == 4
        # Verify all tools are created
        tool_names = [tool.name for tool in tools]
        assert "search_cars" in tool_names
        assert "calculate_financing" in tool_names
        assert "search_kavak_info" in tool_names
        assert "get_car_details" in tool_names
