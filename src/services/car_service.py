from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from src.repositories.car_repository import CarRepository
from src.schemas.car import CarFilter
from src.utils.text_processing import (
    normalize_brand,
    normalize_model,
    find_similar_brand,
    find_similar_model
)


class CarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.car_repo = CarRepository(db)

    async def get_car_by_id(self, car_id: UUID) -> Optional[dict]:
        """Obtiene un auto por ID"""
        car = await self.car_repo.get_by_id(car_id)
        if not car:
            return None
        return {
            "id": str(car.id),
            "stock_id": car.stock_id,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "price": float(car.price),
            "km": car.km,
            "version": car.version,
            "bluetooth": car.bluetooth,
            "car_play": car.car_play,
            "length": float(car.length) if car.length else None,
            "width": float(car.width) if car.width else None,
            "height": float(car.height) if car.height else None,
        }

    async def get_car_by_stock_id(self, stock_id: str) -> Optional[dict]:
        """Obtiene un auto por stock_id"""
        car = await self.car_repo.get_by_stock_id(stock_id)
        if not car:
            return None
        return {
            "id": str(car.id),
            "stock_id": car.stock_id,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "price": float(car.price),
            "km": car.km,
            "version": car.version,
            "bluetooth": car.bluetooth,
            "car_play": car.car_play,
            "length": float(car.length) if car.length else None,
            "width": float(car.width) if car.width else None,
            "height": float(car.height) if car.height else None,
        }

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
    ) -> List[dict]:
        """Busca autos con filtros, usando fuzzy matching para marca/modelo"""
        # Normalizar y corregir marca/modelo
        normalized_make = None
        normalized_model = None

        if make:
            # Obtener marcas disponibles
            available_makes = await self.car_repo.get_all_makes()
            normalized_make = find_similar_brand(make, available_makes)
            if not normalized_make:
                normalized_make = normalize_brand(make)

        if model:
            # Si tenemos marca, obtener modelos de esa marca
            if normalized_make:
                available_models = await self.car_repo.get_models_by_make(normalized_make)
            else:
                available_models = await self.car_repo.get_models_by_make("")

            normalized_model = find_similar_model(model, available_models)
            if not normalized_model:
                normalized_model = normalize_model(model)

        # Crear filtros
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

        # Buscar
        cars = await self.car_repo.search(filters, limit=limit)

        # Convertir a dict
        return [
            {
                "id": str(car.id),
                "stock_id": car.stock_id,
                "make": car.make,
                "model": car.model,
                "year": car.year,
                "price": float(car.price),
                "km": car.km,
                "version": car.version,
                "bluetooth": car.bluetooth,
                "car_play": car.car_play,
                "length": float(car.length) if car.length else None,
                "width": float(car.width) if car.width else None,
                "height": float(car.height) if car.height else None,
            }
            for car in cars
        ]

    async def recommend_cars(
        self,
        preferences: dict,
        limit: int = 10
    ) -> List[dict]:
        """Recomienda autos basado en preferencias"""
        return await self.search_cars(
            make=preferences.get("marca"),
            model=preferences.get("modelo"),
            year=preferences.get("año"),
            min_price=preferences.get("min_price"),
            max_price=preferences.get("max_price"),
            min_year=preferences.get("min_year"),
            max_year=preferences.get("max_year"),
            limit=limit
        )

    async def find_car_by_reference(
        self,
        reference: str,
        last_recommended_cars: Optional[List[dict]] = None,
        selected_car: Optional[dict] = None
    ) -> Optional[dict]:
        """Encuentra un auto por referencia (ID, stock_id, marca/modelo, o referencia contextual)"""
        reference_lower = reference.lower().strip()

        # Referencias contextuales
        if reference_lower in ["ese auto", "el anterior", "ese", "el que me dijiste", "ese carro"]:
            if selected_car:
                return selected_car
            if last_recommended_cars and len(last_recommended_cars) > 0:
                return last_recommended_cars[0]
            return None

        # Buscar por stock_id
        car = await self.car_repo.get_by_stock_id(reference)
        if car:
            return {
                "id": str(car.id),
                "stock_id": car.stock_id,
                "make": car.make,
                "model": car.model,
                "year": car.year,
                "price": float(car.price),
                "km": car.km,
                "version": car.version,
                "bluetooth": car.bluetooth,
                "car_play": car.car_play,
                "length": float(car.length) if car.length else None,
                "width": float(car.width) if car.width else None,
                "height": float(car.height) if car.height else None,
            }

        # Buscar por marca/modelo
        from src.utils.text_processing import extract_car_references
        make, model = extract_car_references(reference)

        if make or model:
            cars = await self.search_cars(make=make, model=model, limit=1)
            if cars:
                return cars[0]

        return None
