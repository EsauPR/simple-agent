import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class Settings:
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://kavak_user:kavak_password@localhost:5432/kavak_db"
    )

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WEBHOOK_SECRET: Optional[str] = os.getenv("TWILIO_WEBHOOK_SECRET", None)

    # Session Management
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    MAX_MESSAGES_IN_HISTORY: int = int(os.getenv("MAX_MESSAGES_IN_HISTORY", "20"))

    # RAG Settings
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # Financing
    FINANCING_INTEREST_RATE: float = float(os.getenv("FINANCING_INTEREST_RATE", "0.10"))
    FINANCING_DEFAULT_DOWN_PAYMENT_PERCENT: float = float(os.getenv("FINANCING_DEFAULT_DOWN_PAYMENT_PERCENT", "0.10"))

    # Scraping
    KAVAK_URL: str = os.getenv("KAVAK_URL", "https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico")

    # API
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()
