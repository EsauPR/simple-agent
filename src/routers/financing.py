from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.services.financing_service import FinancingService
from src.services.car_service import CarService
from src.schemas.financing import FinancingCalculationRequest, FinancingCalculationResponse
from decimal import Decimal

router = APIRouter(prefix="/financing", tags=["financing"])


@router.post("/calculate", response_model=FinancingCalculationResponse)
async def calculate_financing(
    request: FinancingCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calcula planes de financiamiento"""
    financing_service = FinancingService()
    car_service = CarService(db)

    # Obtener precio del auto
    car_price = None
    car_id = None
    stock_id = None

    if request.car_id:
        car = await car_service.get_car_by_id(request.car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        car_price = Decimal(str(car["price"]))
        car_id = request.car_id
        stock_id = car["stock_id"]
    elif request.stock_id:
        car = await car_service.get_car_by_stock_id(request.stock_id)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        car_price = Decimal(str(car["price"]))
        from uuid import UUID as UUIDType
        car_id = UUIDType(car["id"])
        stock_id = request.stock_id
    elif request.car_price:
        car_price = request.car_price
    else:
        raise HTTPException(status_code=400, detail="Must provide car_id, stock_id, or car_price")

    # Calcular planes
    interest_rate = request.interest_rate if request.interest_rate else None
    plans = financing_service.calculate_financing_plans(
        car_price=car_price,
        down_payment=request.down_payment,
        interest_rate=interest_rate,
        min_months=request.min_months,
        max_months=request.max_months
    )

    financed_amount = car_price - request.down_payment
    final_interest_rate = interest_rate if interest_rate else Decimal("0.10")

    return FinancingCalculationResponse(
        car_id=car_id,
        stock_id=stock_id,
        car_price=car_price,
        down_payment=request.down_payment,
        financed_amount=financed_amount,
        interest_rate=final_interest_rate,
        plans=plans
    )
