from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class FinancingPlan(BaseModel):
    months: int
    monthly_payment: Decimal
    total_amount: Decimal
    interest_amount: Decimal


class FinancingCalculationRequest(BaseModel):
    car_id: Optional[UUID] = None
    stock_id: Optional[str] = None
    car_price: Optional[Decimal] = None
    down_payment: Decimal
    interest_rate: Optional[Decimal] = None  # Default 10%
    min_months: int = 36  # 3 years
    max_months: int = 72  # 6 years


class FinancingCalculationResponse(BaseModel):
    car_id: Optional[UUID] = None
    stock_id: Optional[str] = None
    car_price: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    interest_rate: Decimal
    plans: List[FinancingPlan]
