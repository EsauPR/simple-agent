"""Tests for CarService"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

from src.services.car_service import CarService
from src.schemas.car import CarResponse, CarFilter
from src.database.models import Car


@pytest.mark.asyncio
class TestCarService:
    """Tests for CarService"""

    async def test_search_cars_with_filters(self, test_db):
        """Test searching cars with filters"""
        service = CarService(test_db)

        # Mock repository methods
        mock_car = MagicMock(spec=Car)
        mock_car.id = uuid4()
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "FILTER001"
        mock_car.km = 50000
        mock_car.version = "XEI"
        mock_car.bluetooth = True
        mock_car.car_play = False
        mock_car.length = Decimal("4.63")
        mock_car.width = Decimal("1.78")
        mock_car.height = Decimal("1.45")
        mock_car.created_at = datetime.now(timezone.utc)
        mock_car.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=["Toyota", "Honda"])
        service.car_repo.get_models_by_make = AsyncMock(return_value=["Corolla"])
        service.car_repo.search = AsyncMock(return_value=[mock_car])

        # Search by make
        results = await service.search_cars(make="Toyota", limit=10)

        # Verify repository was called correctly
        service.car_repo.get_all_makes.assert_called_once()
        service.car_repo.search.assert_called_once()

        # Verify results
        assert len(results) == 1
        assert all(isinstance(car, CarResponse) for car in results)
        assert results[0].make == "Toyota"

    async def test_search_cars_fuzzy_matching(self, test_db):
        """Test fuzzy matching of brands and models"""
        service = CarService(test_db)

        mock_car = MagicMock(spec=Car)
        mock_car.id = uuid4()
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "FUZZY001"
        mock_car.km = 50000
        mock_car.version = "XEI"
        mock_car.bluetooth = True
        mock_car.car_play = False
        mock_car.length = Decimal("4.63")
        mock_car.width = Decimal("1.78")
        mock_car.height = Decimal("1.45")
        mock_car.created_at = datetime.now(timezone.utc)
        mock_car.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=["Toyota", "Volkswagen"])
        service.car_repo.get_models_by_make = AsyncMock(return_value=["Corolla"])
        service.car_repo.search = AsyncMock(return_value=[mock_car])

        # Search with typo - should still find using fuzzy matching
        results = await service.search_cars(make="toyta", limit=10)  # typo

        # Verify fuzzy matching was attempted
        service.car_repo.get_all_makes.assert_called_once()
        assert len(results) > 0

    async def test_search_cars_by_price_range(self, test_db):
        """Test searching cars by price range"""
        service = CarService(test_db)

        mock_car1 = MagicMock(spec=Car)
        mock_car1.id = uuid4()
        mock_car1.make = "Toyota"
        mock_car1.model = "Corolla"
        mock_car1.year = 2020
        mock_car1.price = Decimal("250000")
        mock_car1.stock_id = "PRICE002"
        mock_car1.km = 50000
        mock_car1.version = "XEI"
        mock_car1.bluetooth = True
        mock_car1.car_play = False
        mock_car1.length = Decimal("4.63")
        mock_car1.width = Decimal("1.78")
        mock_car1.height = Decimal("1.45")
        mock_car1.created_at = datetime.now(timezone.utc)
        mock_car1.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=[])
        service.car_repo.get_models_by_make = AsyncMock(return_value=[])
        service.car_repo.search = AsyncMock(return_value=[mock_car1])

        results = await service.search_cars(min_price=Decimal("200000"), max_price=Decimal("300000"), limit=10)

        # Verify search was called with correct filters
        call_args = service.car_repo.search.call_args
        filters = call_args[0][0]  # First positional argument
        assert isinstance(filters, CarFilter)
        assert filters.min_price == Decimal("200000")
        assert filters.max_price == Decimal("300000")

        assert len(results) > 0
        assert all(200000 <= float(car.price) <= 300000 for car in results)

    async def test_search_cars_by_year_range(self, test_db):
        """Test searching cars by year range"""
        service = CarService(test_db)

        mock_car = MagicMock(spec=Car)
        mock_car.id = uuid4()
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "YEAR002"
        mock_car.km = 50000
        mock_car.version = "XEI"
        mock_car.bluetooth = True
        mock_car.car_play = False
        mock_car.length = Decimal("4.63")
        mock_car.width = Decimal("1.78")
        mock_car.height = Decimal("1.45")
        mock_car.created_at = datetime.now(timezone.utc)
        mock_car.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=[])
        service.car_repo.get_models_by_make = AsyncMock(return_value=[])
        service.car_repo.search = AsyncMock(return_value=[mock_car])

        results = await service.search_cars(min_year=2019, max_year=2021, limit=10)

        # Verify search was called with correct filters
        call_args = service.car_repo.search.call_args
        filters = call_args[0][0]
        assert filters.min_year == 2019
        assert filters.max_year == 2021

        assert len(results) > 0
        assert all(2019 <= car.year <= 2021 for car in results)

    async def test_search_cars_empty_results(self, test_db):
        """Test searching with no matching results"""
        service = CarService(test_db)

        service.car_repo.get_all_makes = AsyncMock(return_value=["Toyota", "Honda"])
        service.car_repo.get_models_by_make = AsyncMock(return_value=[])
        service.car_repo.search = AsyncMock(return_value=[])

        results = await service.search_cars(make="Ferrari", limit=10)

        # Verify repository was called
        service.car_repo.get_all_makes.assert_called_once()
        service.car_repo.search.assert_called_once()

        assert len(results) == 0

    async def test_search_cars_limit(self, test_db):
        """Test that search respects limit"""
        service = CarService(test_db)

        # Create mock cars
        mock_cars = []
        for i in range(5):
            mock_car = MagicMock(spec=Car)
            mock_car.id = uuid4()
            mock_car.make = "Toyota"
            mock_car.model = "Corolla"
            mock_car.year = 2020
            mock_car.price = Decimal("200000")
            mock_car.stock_id = f"LIMIT{i:03d}"
            mock_car.km = 50000
            mock_car.version = "XEI"
            mock_car.bluetooth = True
            mock_car.car_play = False
            mock_car.length = Decimal("4.63")
            mock_car.width = Decimal("1.78")
            mock_car.height = Decimal("1.45")
            mock_car.created_at = datetime.now(timezone.utc)
            mock_car.updated_at = datetime.now(timezone.utc)
            mock_cars.append(mock_car)

        service.car_repo.get_all_makes = AsyncMock(return_value=["Toyota"])
        service.car_repo.get_models_by_make = AsyncMock(return_value=["Corolla"])
        service.car_repo.search = AsyncMock(return_value=mock_cars[:5])

        results = await service.search_cars(limit=5)

        # Verify limit was passed correctly
        call_args = service.car_repo.search.call_args
        # search receives (filters, limit) as positional arguments
        filters = call_args[0][0]  # First positional argument is filters
        limit_arg = call_args[0][1] if len(call_args[0]) > 1 else None

        # Limit can be in filters or as separate argument
        if limit_arg:
            assert limit_arg == 5
        else:
            # If limit is in filters, it should be 5
            assert filters.limit == 5

        assert len(results) <= 5

    async def test_search_cars_with_make_and_model(self, test_db):
        """Test searching with both make and model"""
        service = CarService(test_db)

        mock_car = MagicMock(spec=Car)
        mock_car.id = uuid4()
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "TEST001"
        mock_car.km = 50000
        mock_car.version = "XEI"
        mock_car.bluetooth = True
        mock_car.car_play = False
        mock_car.length = Decimal("4.63")
        mock_car.width = Decimal("1.78")
        mock_car.height = Decimal("1.45")
        mock_car.created_at = datetime.now(timezone.utc)
        mock_car.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=["Toyota"])
        service.car_repo.get_models_by_make = AsyncMock(return_value=["Corolla"])
        service.car_repo.search = AsyncMock(return_value=[mock_car])

        results = await service.search_cars(make="Toyota", model="Corolla", limit=10)

        # Verify both make and model normalization were attempted
        service.car_repo.get_all_makes.assert_called_once()
        service.car_repo.get_models_by_make.assert_called_once_with("Toyota")

        # Verify filters include both make and model
        call_args = service.car_repo.search.call_args
        filters = call_args[0][0]
        assert filters.make is not None
        assert filters.model is not None

        assert len(results) == 1

    async def test_search_cars_with_year_filter(self, test_db):
        """Test searching with year filter"""
        service = CarService(test_db)

        mock_car = MagicMock(spec=Car)
        mock_car.id = uuid4()
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.year = 2020
        mock_car.price = Decimal("200000")
        mock_car.stock_id = "YEAR001"
        mock_car.km = 50000
        mock_car.version = "XEI"
        mock_car.bluetooth = True
        mock_car.car_play = False
        mock_car.length = Decimal("4.63")
        mock_car.width = Decimal("1.78")
        mock_car.height = Decimal("1.45")
        mock_car.created_at = datetime.now(timezone.utc)
        mock_car.updated_at = datetime.now(timezone.utc)

        service.car_repo.get_all_makes = AsyncMock(return_value=[])
        service.car_repo.get_models_by_make = AsyncMock(return_value=[])
        service.car_repo.search = AsyncMock(return_value=[mock_car])

        results = await service.search_cars(year=2020, limit=10)

        # Verify year filter was applied
        call_args = service.car_repo.search.call_args
        filters = call_args[0][0]
        assert filters.year == 2020

        assert len(results) == 1
        assert results[0].year == 2020
