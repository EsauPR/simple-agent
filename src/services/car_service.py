import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from src.repositories.car_repository import CarRepository
from src.schemas.car import CarFilter, CarResponse
from src.utils.text_processing import (
    normalize_brand,
    normalize_model,
    find_similar_brand,
    find_similar_model
)

logger=logging.getLogger(__name__)

class CarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.car_repo = CarRepository(db)

    async def search_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        limit: int = 10
    ) -> List[CarResponse]:
        """Search cars with filters, using fuzzy matching for make/model"""
        # Normalize and correct make/model
        normalized_make = None
        normalized_model = None

        if make:
            # Get available makes
            available_makes = await self.car_repo.get_all_makes()
            normalized_make = find_similar_brand(make, available_makes)
            if not normalized_make:
                normalized_make = normalize_brand(make)

        if model:
            # If we have a make, get models for that make
            if normalized_make:
                available_models = await self.car_repo.get_models_by_make(normalized_make)
            else:
                available_models = await self.car_repo.get_models_by_make("")

            normalized_model = find_similar_model(model, available_models)
            if not normalized_model:
                normalized_model = normalize_model(model)

        logger.debug(f"Search car make {normalized_make} model {normalize_model}")

        # Create filters
        filters = CarFilter(
            make=normalized_make,
            model=normalized_model,
            year=year,
            min_price=min_price,
            max_price=max_price,
            min_year=min_year,
            max_year=max_year,
            limit=limit
        )

        # Search
        cars = await self.car_repo.search(filters, limit=limit)

        # Convert to DTOs
        return [CarResponse.model_validate(car) for car in cars]
