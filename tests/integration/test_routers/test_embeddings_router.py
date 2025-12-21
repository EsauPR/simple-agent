"""Integration tests for embeddings router"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.database.connection import get_db


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client with overridden database"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestEmbeddingsRouter:
    """Tests for embeddings router"""

    async def test_list_embeddings(self, client: TestClient, sample_knowledge_base):
        """Test listing embeddings"""
        response = client.get("/api/v1/embeddings")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_scrape_url_endpoint(self, client: TestClient, test_db, mock_openai_client):
        """Test scrape URL endpoint"""
        with patch("src.services.embedding_service.scraping_service") as mock_scraping:
            mock_scraping.scrape_and_chunk = AsyncMock(return_value=["Chunk 1", "Chunk 2"])

            request_data = {
                "url": "https://test.com",
                "force_update": False
            }

            response = client.post("/api/v1/embeddings/scrape", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "embeddings_created" in data
            assert data["embeddings_created"] == 2
