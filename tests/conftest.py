"""Pytest configuration and fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import StaticPool

from src.database.connection import Base
from src.database.models import Car, KnowledgeBase
from tests.fixtures.sample_data import (
    get_sample_car_data,
    get_sample_cars_data,
    get_sample_embedding,
    get_sample_embeddings,
    get_sample_knowledge_base_data,
)


# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_db(test_db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Fixture that provides a clean database for each test"""
    from sqlalchemy import text

    # Clean up before test
    await test_db_session.execute(text("DELETE FROM knowledge_base"))
    await test_db_session.execute(text("DELETE FROM cars"))
    await test_db_session.commit()

    yield test_db_session

    # Clean up after test
    await test_db_session.execute(text("DELETE FROM knowledge_base"))
    await test_db_session.execute(text("DELETE FROM cars"))
    await test_db_session.commit()


@pytest.fixture
def sample_car_data():
    """Sample car data"""
    return get_sample_car_data()


@pytest.fixture
def sample_cars_data():
    """Multiple sample cars data"""
    return get_sample_cars_data(count=5)


@pytest.fixture
async def sample_cars(test_db: AsyncSession):
    """Create sample cars in database"""
    cars_data = get_sample_cars_data(count=5)
    cars = []
    for car_data in cars_data:
        car = Car(**car_data)
        test_db.add(car)
        cars.append(car)
    await test_db.commit()
    for car in cars:
        await test_db.refresh(car)
    return cars


@pytest.fixture
def sample_embedding():
    """Sample embedding vector"""
    return get_sample_embedding()


@pytest.fixture
def sample_embeddings():
    """Multiple sample embeddings"""
    return get_sample_embeddings(count=3)


@pytest.fixture
async def sample_knowledge_base(test_db: AsyncSession):
    """Create sample knowledge base entry in database"""
    kb_data = get_sample_knowledge_base_data()
    kb = KnowledgeBase(**kb_data)
    test_db.add(kb)
    await test_db.commit()
    await test_db.refresh(kb)
    return kb


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch("src.services.agent.llm_service.ChatOpenAI") as mock_chat, \
         patch("src.services.agent.llm_service.OpenAIEmbeddings") as mock_embeddings:

        # Mock chat model
        mock_chat_instance = MagicMock()
        mock_chat_instance.ainvoke = AsyncMock(return_value=MagicMock(content="Mocked response"))
        mock_chat.return_value = mock_chat_instance

        # Mock embeddings
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(return_value=get_sample_embedding())
        mock_embeddings_instance.aembed_documents = AsyncMock(
            return_value=get_sample_embeddings(count=2)
        )
        mock_embeddings.return_value = mock_embeddings_instance

        yield {
            "chat": mock_chat_instance,
            "embeddings": mock_embeddings_instance,
        }


@pytest.fixture
def mock_twilio_validator():
    """Mock Twilio RequestValidator"""
    with patch("src.routers.chat.RequestValidator") as mock_validator:
        mock_instance = MagicMock()
        mock_instance.validate = MagicMock(return_value=True)
        mock_validator.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def override_get_db(test_db_session: AsyncSession):
    """Override get_db dependency"""
    async def _get_db():
        yield test_db_session

    return _get_db


@pytest.fixture
def mock_runtime():
    """Mock ToolRuntime for langchain tools"""
    from unittest.mock import MagicMock
    from langchain_core.runnables import RunnableConfig

    # Create a simple mock that has the required attributes
    # We'll bypass Pydantic validation by not using invoke/ainvoke directly
    # Instead, we'll call the underlying function
    runtime = MagicMock()
    runtime.state = {}
    runtime.config = RunnableConfig(configurable={"thread_id": "test_thread_123"})
    runtime.context = None  # Can be None according to validation
    runtime.stream_writer = MagicMock()
    runtime.tool_call_id = "test_tool_call_123"
    # For store, we need to mock it as BaseStore instance
    # Since we can't easily create a real BaseStore, we'll use a MagicMock
    # and patch validation if needed
    runtime.store = MagicMock()

    return runtime
