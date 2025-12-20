from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from src.database.connection import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(String, unique=True, nullable=False, index=True)
    km = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    make = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    version = Column(String, nullable=True)
    bluetooth = Column(Boolean, default=False)
    length = Column(Numeric(8, 2), nullable=True)
    width = Column(Numeric(8, 2), nullable=True)
    height = Column(Numeric(8, 2), nullable=True)
    car_play = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    source_url = Column(String, nullable=False, index=True)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    metadata_json = Column("metadata", JSON, nullable=True)  # Using "metadata" as DB column name, metadata_json as attribute
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
