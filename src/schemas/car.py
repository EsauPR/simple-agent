from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID


class CarBase(BaseModel):
    stock_id: str
    km: int
    price: Decimal
    make: str
    model: str
    year: int
    version: Optional[str] = None
    bluetooth: bool = False
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    car_play: bool = False


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    km: Optional[int] = None
    price: Optional[Decimal] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    version: Optional[str] = None
    bluetooth: Optional[bool] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    car_play: Optional[bool] = None


class CarResponse(CarBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CarFilter(BaseModel):
    stock_id: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=50)
