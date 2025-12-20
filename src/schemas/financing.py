from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


class FinancingPlan(BaseModel):
    years: int
    months: int
    monthly_payment: Decimal
    total_amount: Decimal
    interest_amount: Decimal


class FinancingCalculationRequest(BaseModel):
    down_payment: Decimal = Field(..., description="Down payment of the vehicle")
    years: int = Field(..., description="Term in years (3, 4, 5, or 6)")
    car_id: Optional[UUID] = Field(None, description="Vehicle ID")
    stock_id: Optional[str] = Field(None, description="Stock ID of the vehicle")

    @field_validator("years")
    @classmethod
    def validate_years(cls, v: int) -> int:
        if v not in [3, 4, 5, 6]:
            raise ValueError("The term must be 3, 4, 5 or 6 years")
        return v

    @model_validator(mode="after")
    def validate_car_reference(self):
        if not self.car_id and not self.stock_id:
            raise ValueError("Must provide car_id or stock_id")
        if self.car_id and self.stock_id:
            raise ValueError("Must provide only one of car_id or stock_id")
        return self


class FinancingCalculationResponse(BaseModel):
    car_id: Optional[UUID] = None
    stock_id: Optional[str] = None
    car_price: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    interest_rate: Decimal
    plan: FinancingPlan
