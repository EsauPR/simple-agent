from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from src.database.models import KnowledgeBase


class EmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        content: str,
        source_url: str,
        embedding: List[float],
        metadata: Optional[dict] = None
    ) -> KnowledgeBase:
        """Create a new embedding"""
        kb = KnowledgeBase(
            content=content,
            source_url=source_url,
            embedding=embedding,  # pgvector will handle the conversion
            metadata_json=metadata
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def get_by_id(self, embedding_id: UUID) -> Optional[KnowledgeBase]:
        """Get an embedding by ID"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == embedding_id)
        )
        return result.scalar_one_or_none()

    async def get_by_source_url(self, source_url: str) -> List[KnowledgeBase]:
        """Get all embeddings from a URL"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.source_url == source_url)
        )
        return list(result.scalars().all())

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        source_url: Optional[str] = None
    ) -> List[KnowledgeBase]:
        """Search similar embeddings using cosine similarity"""

        # Convert embedding to pgvector format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Use direct SQL query for pgvector
        # The <=> operator calculates cosine distance (smaller is more similar)
        sql = """
            SELECT id, content, source_url, embedding, metadata, created_at, updated_at
            FROM knowledge_base
        """

        params = {"query_embedding": embedding_str, "limit": limit}

        if source_url:
            sql += " WHERE source_url = :source_url"
            params["source_url"] = source_url
            sql += " ORDER BY embedding <=> :query_embedding::vector LIMIT :limit"
        else:
            sql += " ORDER BY embedding <=> :query_embedding::vector LIMIT :limit"

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        # Convert rows to KnowledgeBase objects
        embeddings = []
        for row in rows:
            kb = KnowledgeBase(
                id=row[0],
                content=row[1],
                source_url=row[2],
                embedding=row[3] if row[3] else None,
                metadata_json=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
            embeddings.append(kb)

        return embeddings

    async def delete_by_source_url(self, source_url: str) -> int:
        """Delete all embeddings by source URL"""
        result = await self.db.execute(
            delete(KnowledgeBase).where(KnowledgeBase.source_url == source_url)
        )
        await self.db.commit()
        return result.rowcount

    async def get_all(self, limit: int = 100) -> List[KnowledgeBase]:
        """Get all embeddings (limited)"""
        result = await self.db.execute(
            select(KnowledgeBase).limit(limit)
        )
        return list(result.scalars().all())
