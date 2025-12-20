from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.repositories.car_repository import CarRepository
from src.schemas.car import CarCreate, CarUpdate, CarResponse, CarFilter
from decimal import Decimal

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("", response_model=List[CarResponse])
async def list_cars(
    stock_id: str = None,
    make: str = None,
    model: str = None,
    year: int = None,
    min_price: Decimal = None,
    max_price: Decimal = None,
    min_year: int = None,
    max_year: int = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List cars with optional filters"""
    filters = CarFilter(
        stock_id=stock_id,
        make=make,
        model=model,
        year=year,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        limit=limit
    )

    car_repo = CarRepository(db)
    cars = await car_repo.search(filters, limit=limit)
    return [CarResponse.model_validate(car) for car in cars]


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(
    car_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a car by ID"""
    car_repo = CarRepository(db)
    car = await car_repo.get_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarResponse.model_validate(car)


@router.post("", response_model=CarResponse, status_code=201)
async def create_car(
    car_data: CarCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new car"""
    car_repo = CarRepository(db)

    existing = await car_repo.get_by_stock_id(car_data.stock_id)
    if existing:
        raise HTTPException(status_code=400, detail="Car with this stock_id already exists")

    car = await car_repo.create(car_data.model_dump())
    return CarResponse.model_validate(car)


@router.put("/{car_id}", response_model=CarResponse)
async def update_car(
    car_id: UUID,
    car_data: CarUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a car"""
    car_repo = CarRepository(db)
    car = await car_repo.get_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    update_data = car_data.model_dump(exclude_unset=True)
    car = await car_repo.update(car, update_data)
    return CarResponse.model_validate(car)


@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a car"""
    car_repo = CarRepository(db)
    car = await car_repo.get_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    await car_repo.delete(car)
    return None


@router.post("/bulk", status_code=201)
async def bulk_create_cars(
    cars_data: List[CarCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create multiple cars"""
    car_repo = CarRepository(db)
    created = []
    errors = []

    for car_data in cars_data:
        try:
            existing = await car_repo.get_by_stock_id(car_data.stock_id)
            if existing:
                errors.append(f"Car {car_data.stock_id} already exists")
                continue

            car = await car_repo.create(car_data.model_dump())
            created.append(CarResponse.model_validate(car))
        except Exception as e:
            errors.append(f"Error creating car {car_data.stock_id}: {str(e)}")

    return {
        "created": len(created),
        "errors": len(errors),
        "cars": created,
        "error_details": errors
    }
