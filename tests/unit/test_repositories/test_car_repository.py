"""Tests for CarRepository"""
import pytest
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from src.repositories.car_repository import CarRepository
from src.schemas.car import CarFilter
from tests.fixtures.sample_data import get_sample_car_data


@pytest.mark.asyncio
class TestCarRepository:
    """Tests for CarRepository"""

    async def test_create_car(self, test_db):
        """Test creating a car"""
        repo = CarRepository(test_db)
        car_data = get_sample_car_data(stock_id="CREATE001")

        car = await repo.create(car_data)

        assert car.id is not None
        assert car.stock_id == "CREATE001"
        assert car.make == "Toyota"
        assert car.model == "Corolla"

    async def test_get_by_id(self, test_db):
        """Test getting a car by ID"""
        repo = CarRepository(test_db)
        car_data = get_sample_car_data(stock_id="GET001")
        car = await repo.create(car_data)
        car_id = car.id

        retrieved = await repo.get_by_id(car_id)

        assert retrieved is not None
        assert retrieved.id == car_id
        assert retrieved.stock_id == "GET001"

    async def test_get_by_id_not_found(self, test_db):
        """Test getting a car by ID that doesn't exist"""
        repo = CarRepository(test_db)
        fake_id = uuid4()

        retrieved = await repo.get_by_id(fake_id)

        assert retrieved is None

    async def test_get_by_stock_id(self, test_db):
        """Test getting a car by stock_id"""
        repo = CarRepository(test_db)
        car_data = get_sample_car_data(stock_id="STOCK001")
        await repo.create(car_data)

        retrieved = await repo.get_by_stock_id("STOCK001")

        assert retrieved is not None
        assert retrieved.stock_id == "STOCK001"

    async def test_get_by_stock_id_not_found(self, test_db):
        """Test getting a car by stock_id that doesn't exist"""
        repo = CarRepository(test_db)

        retrieved = await repo.get_by_stock_id("NONEXISTENT")

        assert retrieved is None

    async def test_search_with_filters(self, test_db):
        """Test searching cars with filters"""
        repo = CarRepository(test_db)

        # Create test cars
        await repo.create(get_sample_car_data(stock_id="SEARCH001", make="Toyota", model="Corolla", year=2020, price=Decimal("200000")))
        await repo.create(get_sample_car_data(stock_id="SEARCH002", make="Honda", model="Civic", year=2021, price=Decimal("250000")))
        await repo.create(get_sample_car_data(stock_id="SEARCH003", make="Toyota", model="Camry", year=2020, price=Decimal("300000")))

        # Search by make
        filters = CarFilter(make="Toyota", limit=10)
        results = await repo.search(filters, limit=10)

        assert len(results) == 2
        assert all(car.make == "Toyota" for car in results)

    async def test_search_by_price_range(self, test_db):
        """Test searching cars by price range"""
        repo = CarRepository(test_db)

        await repo.create(get_sample_car_data(stock_id="PRICE001", price=Decimal("150000")))
        await repo.create(get_sample_car_data(stock_id="PRICE002", price=Decimal("250000")))
        await repo.create(get_sample_car_data(stock_id="PRICE003", price=Decimal("350000")))

        filters = CarFilter(min_price=Decimal("200000"), max_price=Decimal("300000"), limit=10)
        results = await repo.search(filters, limit=10)

        assert len(results) == 1
        assert results[0].stock_id == "PRICE002"

    async def test_search_by_year_range(self, test_db):
        """Test searching cars by year range"""
        repo = CarRepository(test_db)

        await repo.create(get_sample_car_data(stock_id="YEAR001", year=2018))
        await repo.create(get_sample_car_data(stock_id="YEAR002", year=2020))
        await repo.create(get_sample_car_data(stock_id="YEAR003", year=2022))

        filters = CarFilter(min_year=2019, max_year=2021, limit=10)
        results = await repo.search(filters, limit=10)

        assert len(results) == 1
        assert results[0].stock_id == "YEAR002"

    async def test_search_excludes_deleted(self, test_db):
        """Test that search excludes soft-deleted cars"""
        repo = CarRepository(test_db)

        car_data = get_sample_car_data(stock_id="DELETED001")
        car = await repo.create(car_data)

        # Soft delete the car
        await repo.delete(car)

        # Try to get it by ID
        retrieved = await repo.get_by_id(car.id)
        assert retrieved is None

        # Try to get it by stock_id
        retrieved = await repo.get_by_stock_id("DELETED001")
        assert retrieved is None

        # Search should not return it
        filters = CarFilter(limit=10)
        results = await repo.search(filters, limit=10)
        assert len(results) == 0

    async def test_get_all_makes(self, test_db):
        """Test getting all unique makes"""
        repo = CarRepository(test_db)

        await repo.create(get_sample_car_data(stock_id="MAKE001", make="Toyota"))
        await repo.create(get_sample_car_data(stock_id="MAKE002", make="Honda"))
        await repo.create(get_sample_car_data(stock_id="MAKE003", make="Toyota"))

        makes = await repo.get_all_makes()

        assert "Toyota" in makes
        assert "Honda" in makes
        assert makes.count("Toyota") == 1  # Should be unique

    async def test_get_models_by_make(self, test_db):
        """Test getting models by make"""
        repo = CarRepository(test_db)

        await repo.create(get_sample_car_data(stock_id="MODEL001", make="Toyota", model="Corolla"))
        await repo.create(get_sample_car_data(stock_id="MODEL002", make="Toyota", model="Camry"))
        await repo.create(get_sample_car_data(stock_id="MODEL003", make="Honda", model="Civic"))

        models = await repo.get_models_by_make("Toyota")

        assert "Corolla" in models
        assert "Camry" in models
        assert "Civic" not in models

    async def test_update_car(self, test_db):
        """Test updating a car"""
        repo = CarRepository(test_db)
        car_data = get_sample_car_data(stock_id="UPDATE001")
        car = await repo.create(car_data)

        update_data = {"price": Decimal("250000"), "km": 60000}
        updated = await repo.update(car, update_data)

        assert updated.price == Decimal("250000")
        assert updated.km == 60000
        assert updated.stock_id == "UPDATE001"  # Other fields unchanged

    async def test_soft_delete_car(self, test_db):
        """Test soft deleting a car"""
        repo = CarRepository(test_db)
        car_data = get_sample_car_data(stock_id="DELETE001")
        car = await repo.create(car_data)

        await repo.delete(car)
        await test_db.refresh(car)

        assert car.deleted_at is not None
        assert isinstance(car.deleted_at, datetime)

    async def test_search_by_make_model(self, test_db):
        """Test searching by make and model"""
        repo = CarRepository(test_db)

        await repo.create(get_sample_car_data(stock_id="MM001", make="Toyota", model="Corolla"))
        await repo.create(get_sample_car_data(stock_id="MM002", make="Toyota", model="Camry"))
        await repo.create(get_sample_car_data(stock_id="MM003", make="Honda", model="Civic"))

        results = await repo.search_by_make_model(make="Toyota", model="Corolla", limit=10)

        assert len(results) == 1
        assert results[0].stock_id == "MM001"
