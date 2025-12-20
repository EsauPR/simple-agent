from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database.models import Car
from src.schemas.car import CarFilter


class CarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _not_deleted_filter(self):
        """Helper to filter out soft-deleted records"""
        return Car.deleted_at.is_(None)

    async def get_by_id(self, car_id: UUID) -> Optional[Car]:
        """Get a car by ID (excluding soft-deleted)"""
        result = await self.db.execute(
            select(Car).where(and_(Car.id == car_id, self._not_deleted_filter()))
        )
        return result.scalar_one_or_none()

    async def get_by_stock_id(self, stock_id: str) -> Optional[Car]:
        """Get a car by stock_id (excluding soft-deleted)"""
        result = await self.db.execute(
            select(Car).where(and_(Car.stock_id == stock_id, self._not_deleted_filter()))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        filters: CarFilter,
        limit: int = 10
    ) -> List[Car]:
        """Search cars with filters (excluding soft-deleted)"""
        query = select(Car)
        conditions = [self._not_deleted_filter()]

        if filters.stock_id:
            conditions.append(Car.stock_id == filters.stock_id)

        if filters.make:
            conditions.append(Car.make.ilike(f"%{filters.make}%"))

        if filters.model:
            conditions.append(Car.model.ilike(f"%{filters.model}%"))

        if filters.year:
            conditions.append(Car.year == filters.year)

        if filters.min_year:
            conditions.append(Car.year >= filters.min_year)

        if filters.max_year:
            conditions.append(Car.year <= filters.max_year)

        if filters.min_price:
            conditions.append(Car.price >= filters.min_price)

        if filters.max_price:
            conditions.append(Car.price <= filters.max_price)

        query = query.where(and_(*conditions))

        # sort by year descending, price ascending, km ascending
        query = query.order_by(Car.year.desc(), Car.price.asc(), Car.km.asc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_by_make_model(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 10
    ) -> List[Car]:
        """Search cars by make and/or model (case-insensitive, excluding soft-deleted)"""
        query = select(Car)
        conditions = [self._not_deleted_filter()]

        if make:
            conditions.append(Car.make.ilike(f"%{make}%"))

        if model:
            conditions.append(Car.model.ilike(f"%{model}%"))

        query = query.where(and_(*conditions))

        query = query.order_by(Car.year.desc(), Car.price.asc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_makes(self) -> List[str]:
        """Get all unique makes (excluding soft-deleted)"""
        result = await self.db.execute(
            select(Car.make).where(self._not_deleted_filter()).distinct()
        )
        return [row[0] for row in result.all()]

    async def get_models_by_make(self, make: str) -> List[str]:
        """Get all models of a make (excluding soft-deleted)"""
        result = await self.db.execute(
            select(Car.model).where(
                and_(Car.make.ilike(f"%{make}%"), self._not_deleted_filter())
            ).distinct()
        )
        return [row[0] for row in result.all()]

    async def create(self, car_data: dict) -> Car:
        """Create a new car"""
        car = Car(**car_data)
        self.db.add(car)
        await self.db.commit()
        await self.db.refresh(car)
        return car

    async def update(self, car: Car, car_data: dict) -> Car:
        """Update a car"""
        for key, value in car_data.items():
            setattr(car, key, value)
        await self.db.commit()
        await self.db.refresh(car)
        return car

    async def delete(self, car: Car) -> None:
        """Soft delete a car by setting deleted_at timestamp"""
        car.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(car)
