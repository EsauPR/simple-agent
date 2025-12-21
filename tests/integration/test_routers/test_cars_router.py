"""Integration tests for cars router"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app
from src.database.connection import get_db
from tests.fixtures.sample_data import get_sample_car_data
from src.repositories.car_repository import CarRepository

@pytest.fixture
def client(test_db, override_get_db):
    """Create test client with overridden database"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestCarsRouter:
    """Tests for cars router"""

    async def test_list_cars(self, client: TestClient, sample_cars):
        """Test listing cars"""
        response = client.get("/api/v1/cars")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_cars_with_filters(self, client: TestClient, test_db):
        """Test listing cars with filters"""
        repo = CarRepository(test_db)
        await repo.create(get_sample_car_data(stock_id="FILTER001", make="Toyota"))

        response = client.get("/api/v1/cars?make=Toyota")

        assert response.status_code == 200
        data = response.json()
        assert all(car["make"] == "Toyota" for car in data)

    async def test_get_car_by_id(self, client: TestClient, test_db):
        """Test getting a car by ID"""
        repo = CarRepository(test_db)
        car = await repo.create(get_sample_car_data(stock_id="GET001"))

        response = client.get(f"/api/v1/cars/{car.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(car.id)
        assert data["stock_id"] == "GET001"

    async def test_get_car_by_id_not_found(self, client: TestClient):
        """Test getting a car that doesn't exist"""
        fake_id = uuid4()
        response = client.get(f"/api/v1/cars/{fake_id}")

        assert response.status_code == 404

    async def test_create_car(self, client: TestClient):
        """Test creating a car"""
        car_data = get_sample_car_data(stock_id="CREATE001")
        car_dict = {k: str(v) if isinstance(v, type(car_data["price"])) else v
                   for k, v in car_data.items()}

        response = client.post("/api/v1/cars", json=car_dict)

        assert response.status_code == 201
        data = response.json()
        assert data["stock_id"] == "CREATE001"

    async def test_create_car_duplicate_stock_id(self, client: TestClient, test_db):
        """Test creating a car with duplicate stock_id"""
        repo = CarRepository(test_db)
        await repo.create(get_sample_car_data(stock_id="DUPLICATE001"))

        car_data = get_sample_car_data(stock_id="DUPLICATE001")
        car_dict = {k: str(v) if isinstance(v, type(car_data["price"])) else v
                   for k, v in car_data.items()}

        response = client.post("/api/v1/cars", json=car_dict)

        assert response.status_code == 400

    async def test_update_car(self, client: TestClient, test_db):
        """Test updating a car"""
        repo = CarRepository(test_db)
        car = await repo.create(get_sample_car_data(stock_id="UPDATE001"))

        update_data = {"price": "250000.00", "km": 60000}
        response = client.put(f"/api/v1/cars/{car.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["km"] == 60000

    async def test_delete_car(self, client: TestClient, test_db):
        """Test deleting a car"""
        repo = CarRepository(test_db)
        car = await repo.create(get_sample_car_data(stock_id="DELETE001"))

        response = client.delete(f"/api/v1/cars/{car.id}")

        assert response.status_code == 204

        # Verify it's soft deleted
        retrieved = await repo.get_by_id(car.id)
        assert retrieved is None
