from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import init_db, close_db
from src.routers import chat, cars, financing, embeddings
from src.middleware import LoggingMiddleware
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized")

    yield

    # Shutdown
    await close_db()
    print("Application shutdown")


app = FastAPI(
    title="Kavak Commercial Bot API",
    description="API for the Kavak Commercial Bot with WhatsApp integration and LangChain",
    version="0.0.1",
    lifespan=lifespan
)

# Logging middleware (must be added before CORS)
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
