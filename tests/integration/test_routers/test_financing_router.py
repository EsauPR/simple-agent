"""Integration tests for financing router"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

from src.main import app
from src.database.connection import get_db
from src.dependencies.auth import auth
from tests.fixtures.sample_data import get_sample_car_data


@pytest.fixture
def client(test_db, override_get_db, override_auth):
    """Create test client with overridden database and auth"""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth] = override_auth
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestFinancingRouter:
    """Tests for financing router"""

    async def test_calculate_financing(self, client: TestClient, test_db):
        """Test calculating financing"""
        from src.repositories.car_repository import CarRepository
        repo = CarRepository(test_db)
        await repo.create(get_sample_car_data(
            stock_id="FIN001",
            price=Decimal("200000")
        ))

        request_data = {
            "stock_id": "FIN001",
            "down_payment": "40000.00",
            "years": 3
        }

        response = client.post("/api/v1/financing/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"]["years"] == 3
        assert data["plan"]["months"] == 36

    async def test_calculate_financing_invalid_years(self, client: TestClient, test_db):
        """Test calculating financing with invalid years"""
        from src.repositories.car_repository import CarRepository
        repo = CarRepository(test_db)
        await repo.create(get_sample_car_data(stock_id="FIN002", price=Decimal("200000")))

        request_data = {
            "stock_id": "FIN002",
            "down_payment": "40000.00",
            "years": 2  # Invalid
        }

        response = client.post("/api/v1/financing/calculate", json=request_data)

        assert response.status_code == 422

    async def test_calculate_financing_down_payment_too_high(self, client: TestClient, test_db):
        """Test calculating financing with down payment >= car price"""
        from src.repositories.car_repository import CarRepository
        repo = CarRepository(test_db)
        await repo.create(get_sample_car_data(stock_id="FIN003", price=Decimal("200000")))

        request_data = {
            "stock_id": "FIN003",
            "down_payment": "250000.00",  # Higher than price
            "years": 3
        }

        response = client.post("/api/v1/financing/calculate", json=request_data)

        assert response.status_code == 400

    async def test_calculate_financing_car_not_found(self, client: TestClient):
        """Test calculating financing for non-existent car"""
        request_data = {
            "stock_id": "NONEXISTENT",
            "down_payment": "40000.00",
            "years": 3
        }

        response = client.post("/api/v1/financing/calculate", json=request_data)

        assert response.status_code == 404
