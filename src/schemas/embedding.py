from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class EmbeddingCreate(BaseModel):
    content: str
    source_url: str
    metadata: Optional[dict] = None


class EmbeddingResponse(BaseModel):
    id: UUID
    content: str
    source_url: str
    metadata: Optional[dict] = Field(None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ScrapeRequest(BaseModel):
    url: str
    force_update: bool = False


class ScrapeResponse(BaseModel):
    message: str
    embeddings_created: int
    embeddings_deleted: int
