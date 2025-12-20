-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create index for vector similarity search on knowledge_base
-- This will be created after the table is created by SQLAlchemy
-- But we can prepare the index creation here

-- Note: Tables will be created by SQLAlchemy models
-- Indexes for vector search will be created via Alembic or manually:
-- CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
