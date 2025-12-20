from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get a database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables and extensions"""
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

        # Create vector index for knowledge_base (if table exists)
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx
                ON knowledge_base
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
        except Exception:
            pass


async def close_db():
    """Close database connections"""
    await engine.dispose()
