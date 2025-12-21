from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import init_db, close_db
from src.routers import chat, cars, financing, embeddings, auth
from src.middleware import LoggingMiddleware
from src.services.message_processor import message_processor
from src.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Start message processor cron job
    logger.info("Starting message processor...")
    await message_processor.start()
    logger.info("Message processor started")

    yield

    # Stop message processor cron job
    logger.info("Stopping message processor...")
    await message_processor.stop()
    logger.info("Message processor stopped")

    await close_db()
    logger.info("Application shutdown")


app = FastAPI(
    title="Kavak Commercial Bot API",
    description="API for the Kavak Commercial Bot with WhatsApp integration and LangChain",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(cars.router, prefix=settings.API_V1_PREFIX)
app.include_router(financing.router, prefix=settings.API_V1_PREFIX)
app.include_router(embeddings.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)



@app.get("/")
async def root():
    return {
        "message": "Kavak Commercial Bot API",
        "version": "0.0.1",
        "description": "Bot comercial with Agentic feature",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
