from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.agent.llm_service import llm_service
from src.services.scraping_service import scraping_service
from src.repositories.embedding_repository import EmbeddingRepository
from src.config import settings


class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_repo = EmbeddingRepository(db)

    async def generate_and_store_embedding(
        self,
        content: str,
        source_url: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Generate embedding and store it"""
        embedding = await llm_service.generate_embedding(content)
        await self.embedding_repo.create(content, source_url, embedding, metadata)

    async def search_similar(
        self,
        query: str,
        limit: int = None,
        source_url: Optional[str] = None
    ) -> List[dict]:
        """Search for similar content using embeddings"""
        if limit is None:
            limit = settings.RAG_TOP_K

        # Generate embedding of the query
        query_embedding = await llm_service.generate_embedding(query)

        # Search for similar embeddings
        results = await self.embedding_repo.search_similar(
            query_embedding,
            limit=limit,
            source_url=source_url
        )

        return [
            {
                "id": str(result.id),
                "content": result.content,
                "source_url": result.source_url,
                "metadata": result.metadata_json
            }
            for result in results
        ]

    async def scrape_and_store(
        self,
        url: str,
        force_update: bool = False
    ) -> dict:
        """Scrape an URL, generate embeddings and store them"""
        # Si force_update, eliminar embeddings existentes
        deleted_count = 0
        if force_update:
            deleted_count = await self.embedding_repo.delete_by_source_url(url)

        # Scrape and chunk
        chunks = await scraping_service.scrape_and_chunk(url)

        # Generate and store embeddings
        created_count = 0
        for i, chunk in enumerate(chunks):
            metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "url": url
            }
            await self.generate_and_store_embedding(chunk, url, metadata)
            created_count += 1

        return {
            "embeddings_created": created_count,
            "embeddings_deleted": deleted_count,
            "chunks_processed": len(chunks)
        }
