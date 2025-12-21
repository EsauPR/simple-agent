"""Tests for EmbeddingService"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.services.embedding_service import EmbeddingService
from src.schemas.embedding import EmbeddingSearchResult, ScrapeResult
from src.database.models import KnowledgeBase
from tests.fixtures.sample_data import get_sample_embedding


@pytest.mark.asyncio
class TestEmbeddingService:
    """Tests for EmbeddingService"""

    async def test_generate_and_store_embedding(self, test_db):
        """Test generating and storing an embedding"""
        service = EmbeddingService(test_db)

        content = "Test content"
        source_url = "https://test.com"
        metadata = {"test": "metadata"}
        mock_embedding = get_sample_embedding()

        with patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_embedding

            # Mock the repository create method
            mock_kb = MagicMock(spec=KnowledgeBase)
            mock_kb.id = uuid4()
            mock_kb.content = content
            mock_kb.source_url = source_url
            mock_kb.metadata_json = metadata

            service.embedding_repo.create = AsyncMock(return_value=mock_kb)

            # Call the method
            await service.generate_and_store_embedding(content, source_url, metadata)

            # Verify llm_service was called with correct content
            mock_llm.assert_called_once_with(content)

            # Verify repository was called with correct parameters
            service.embedding_repo.create.assert_called_once_with(
                content,
                source_url,
                mock_embedding,
                metadata
            )

    async def test_generate_and_store_embedding_no_metadata(self, test_db):
        """Test generating and storing an embedding without metadata"""
        service = EmbeddingService(test_db)

        content = "Test content"
        source_url = "https://test.com"
        mock_embedding = get_sample_embedding()

        with patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_embedding

            mock_kb = MagicMock(spec=KnowledgeBase)
            service.embedding_repo.create = AsyncMock(return_value=mock_kb)

            await service.generate_and_store_embedding(content, source_url)

            mock_llm.assert_called_once_with(content)
            service.embedding_repo.create.assert_called_once_with(
                content,
                source_url,
                mock_embedding,
                None
            )

    async def test_search_similar(self, test_db):
        """Test searching for similar content"""
        service = EmbeddingService(test_db)

        query = "test query"
        limit = 5
        mock_query_embedding = get_sample_embedding()

        # Create mock results from repository
        mock_result1 = MagicMock(spec=KnowledgeBase)
        mock_result1.id = uuid4()
        mock_result1.content = "Result 1 content"
        mock_result1.source_url = "https://test.com/page1"
        mock_result1.metadata_json = {"chunk_index": 0}

        mock_result2 = MagicMock(spec=KnowledgeBase)
        mock_result2.id = uuid4()
        mock_result2.content = "Result 2 content"
        mock_result2.source_url = "https://test.com/page2"
        mock_result2.metadata_json = None

        mock_results = [mock_result1, mock_result2]

        with patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_query_embedding

            service.embedding_repo.search_similar = AsyncMock(return_value=mock_results)

            # Call the method
            results = await service.search_similar(query, limit=limit)

            # Verify llm_service was called with query
            mock_llm.assert_called_once_with(query)

            # Verify repository was called with correct parameters
            service.embedding_repo.search_similar.assert_called_once_with(
                mock_query_embedding,
                limit=limit,
                source_url=None
            )

            # Verify results are correctly formatted
            assert len(results) == 2
            assert all(isinstance(r, EmbeddingSearchResult) for r in results)
            assert results[0].content == "Result 1 content"
            assert results[0].metadata == {"chunk_index": 0}
            assert results[1].content == "Result 2 content"
            assert results[1].metadata is None

    async def test_search_similar_with_source_url(self, test_db):
        """Test searching for similar content with source_url filter"""
        service = EmbeddingService(test_db)

        query = "test query"
        source_url = "https://test.com"
        mock_query_embedding = get_sample_embedding()
        mock_results = []

        with patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm, \
             patch('src.services.embedding_service.settings.RAG_TOP_K', 5):
            mock_llm.return_value = mock_query_embedding

            service.embedding_repo.search_similar = AsyncMock(return_value=mock_results)

            results = await service.search_similar(query, source_url=source_url)

            mock_llm.assert_called_once_with(query)
            service.embedding_repo.search_similar.assert_called_once_with(
                mock_query_embedding,
                limit=5,  # Should use default from settings
                source_url=source_url
            )
            assert len(results) == 0

    async def test_search_similar_uses_default_limit(self, test_db):
        """Test that search_similar uses RAG_TOP_K when limit is None"""
        service = EmbeddingService(test_db)

        query = "test query"
        mock_query_embedding = get_sample_embedding()
        mock_results = []

        with patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm, \
             patch('src.services.embedding_service.settings.RAG_TOP_K', 10):
            mock_llm.return_value = mock_query_embedding

            service.embedding_repo.search_similar = AsyncMock(return_value=mock_results)

            await service.search_similar(query, limit=None)

            service.embedding_repo.search_similar.assert_called_once_with(
                mock_query_embedding,
                limit=10,
                source_url=None
            )

    async def test_scrape_and_store(self, test_db):
        """Test scraping and storing embeddings"""
        service = EmbeddingService(test_db)

        url = "https://test.com"
        chunks = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        mock_embedding = get_sample_embedding()

        with patch('src.services.embedding_service.scraping_service.scrape_and_chunk', new_callable=AsyncMock) as mock_scrape, \
             patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm:

            mock_scrape.return_value = chunks
            mock_llm.return_value = mock_embedding

            # Mock repository methods
            mock_kb = MagicMock(spec=KnowledgeBase)
            service.embedding_repo.create = AsyncMock(return_value=mock_kb)
            service.embedding_repo.delete_by_source_url = AsyncMock(return_value=0)

            # Call the method
            result = await service.scrape_and_store(url, force_update=False)

            # Verify scraping was called
            mock_scrape.assert_called_once_with(url)

            # Verify delete was NOT called (force_update=False)
            service.embedding_repo.delete_by_source_url.assert_not_called()

            # Verify embeddings were created for each chunk
            assert mock_llm.call_count == len(chunks)
            assert service.embedding_repo.create.call_count == len(chunks)

            # Verify metadata was set correctly for each chunk
            for i, call in enumerate(service.embedding_repo.create.call_args_list):
                args, kwargs = call
                assert args[0] == chunks[i]  # content
                assert args[1] == url  # source_url
                assert args[2] == mock_embedding  # embedding
                assert args[3]["chunk_index"] == i
                assert args[3]["total_chunks"] == len(chunks)
                assert args[3]["url"] == url

            # Verify result
            assert isinstance(result, ScrapeResult)
            assert result.embeddings_created == len(chunks)
            assert result.embeddings_deleted == 0
            assert result.chunks_processed == len(chunks)

    async def test_scrape_and_store_with_force_update(self, test_db):
        """Test scraping and storing with force_update=True"""
        service = EmbeddingService(test_db)

        url = "https://test.com"
        chunks = ["Chunk 1", "Chunk 2"]
        deleted_count = 3
        mock_embedding = get_sample_embedding()

        with patch('src.services.embedding_service.scraping_service.scrape_and_chunk', new_callable=AsyncMock) as mock_scrape, \
             patch('src.services.embedding_service.llm_service.generate_embedding', new_callable=AsyncMock) as mock_llm:

            mock_scrape.return_value = chunks
            mock_llm.return_value = mock_embedding

            mock_kb = MagicMock(spec=KnowledgeBase)
            service.embedding_repo.create = AsyncMock(return_value=mock_kb)
            service.embedding_repo.delete_by_source_url = AsyncMock(return_value=deleted_count)

            result = await service.scrape_and_store(url, force_update=True)

            # Verify delete was called first
            service.embedding_repo.delete_by_source_url.assert_called_once_with(url)

            # Verify scraping was called
            mock_scrape.assert_called_once_with(url)

            # Verify embeddings were created
            assert service.embedding_repo.create.call_count == len(chunks)

            # Verify result includes deleted count
            assert result.embeddings_deleted == deleted_count
            assert result.embeddings_created == len(chunks)
            assert result.chunks_processed == len(chunks)

    async def test_scrape_and_store_empty_chunks(self, test_db):
        """Test scraping and storing with empty chunks"""
        service = EmbeddingService(test_db)

        url = "https://test.com"
        chunks = []

        with patch('src.services.embedding_service.scraping_service.scrape_and_chunk', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = chunks

            service.embedding_repo.delete_by_source_url = AsyncMock(return_value=0)

            result = await service.scrape_and_store(url)

            assert result.embeddings_created == 0
            assert result.chunks_processed == 0
            assert result.embeddings_deleted == 0
