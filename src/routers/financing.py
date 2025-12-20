from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.services.financing_service import FinancingService
from src.repositories.car_repository import CarRepository
from src.schemas.financing import FinancingCalculationRequest, FinancingCalculationResponse

router = APIRouter(prefix="/financing", tags=["financing"])


@router.post("/calculate", response_model=FinancingCalculationResponse)
async def calculate_financing(
    request: FinancingCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calculate financing plan for a specific car and term"""
    financing_service = FinancingService()
    car_repo = CarRepository(db)

    car = None
    if request.car_id:
        car = await car_repo.get_by_id(request.car_id)
    elif request.stock_id:
        car = await car_repo.get_by_stock_id(request.stock_id)

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # Validate down payment
    if request.down_payment >= car.price:
        raise HTTPException(
            status_code=400,
            detail="El enganche no puede ser mayor o igual al precio del vehículo"
        )

    # Calculate financing plan
    try:
        plan = financing_service.calculate_financing_plan(
            car_price=car.price,
            down_payment=request.down_payment,
            years=request.years
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    financed_amount = car.price - request.down_payment
    interest_rate = financing_service.interest_rate

    return FinancingCalculationResponse(
        car_id=car.id,
        stock_id=car.stock_id,
        car_price=car.price,
        down_payment=request.down_payment,
        financed_amount=financed_amount,
        interest_rate=interest_rate,
        plan=plan
    )
