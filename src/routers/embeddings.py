from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.services.embedding_service import EmbeddingService
from src.schemas.embedding import ScrapeRequest, ScrapeResponse, EmbeddingResponse

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_and_store(
    request: ScrapeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Scrape an URL and store embeddings"""
    embedding_service = EmbeddingService(db)

    try:
        result = await embedding_service.scrape_and_store(
            request.url,
            force_update=request.force_update
        )

        return ScrapeResponse(
            message=f"Successfully scraped and created {result['embeddings_created']} embeddings",
            embeddings_created=result["embeddings_created"],
            embeddings_deleted=result["embeddings_deleted"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[EmbeddingResponse])
async def list_embeddings(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List embeddings"""
    from src.repositories.embedding_repository import EmbeddingRepository

    embedding_repo = EmbeddingRepository(db)
    embeddings = await embedding_repo.get_all(limit=limit)
    return [EmbeddingResponse.model_validate(emb) for emb in embeddings]


@router.delete("/{embedding_id}", status_code=204)
async def delete_embedding(
    embedding_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an embedding"""
    from src.repositories.embedding_repository import EmbeddingRepository

    embedding_repo = EmbeddingRepository(db)
    embedding = await embedding_repo.get_by_id(embedding_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")

    await db.delete(embedding)
    await db.commit()
    return None
