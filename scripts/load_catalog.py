#!/usr/bin/env python3
"""
Script para cargar el catálogo de autos desde CSV a la base de datos.
Se ejecuta automáticamente al inicializar la DB o manualmente.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database.connection import init_db
from src.utils.csv_loader import load_cars_from_csv
from src.config import settings


async def main():
    """Load the catalog from CSV"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await init_db()

    csv_path = Path(__file__).parent.parent / "sample_caso_ai_engineer.csv"

    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    async with async_session() as db:
        print(f"Loading cars from {csv_path}...")
        cars_created = await load_cars_from_csv(str(csv_path), db)
        print(f"Successfully loaded {cars_created} cars")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
