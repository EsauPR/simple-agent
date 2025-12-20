from decimal import Decimal
from typing import Optional
from math import pow
from src.config import settings
from src.schemas.financing import FinancingPlan


class FinancingService:
    def __init__(self):
        self.interest_rate = Decimal(str(settings.FINANCING_INTEREST_RATE))
        self.default_down_payment_percent = Decimal(str(settings.FINANCING_DEFAULT_DOWN_PAYMENT_PERCENT))

    def calculate_monthly_payment(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        months: int
    ) -> Decimal:
        """Calculate the monthly payment using the compound interest formula"""
        if principal <= 0:
            return Decimal("0")

        if months <= 0:
            return Decimal("0")

        # Monthly rate
        monthly_rate = annual_rate / Decimal("12")

        # If the rate is 0, simply divide the principal by the months
        if monthly_rate == 0:
            return principal / Decimal(str(months))

        # Formula: P = (P * r * (1 + r)^n) / ((1 + r)^n - 1)
        # Where P = principal, r = monthly rate, n = number of months

        one_plus_rate = Decimal("1") + monthly_rate
        one_plus_rate_power = Decimal(str(pow(float(one_plus_rate), months)))

        numerator = principal * monthly_rate * one_plus_rate_power
        denominator = one_plus_rate_power - Decimal("1")

        if denominator == 0:
            return principal / Decimal(str(months))

        monthly_payment = numerator / denominator

        return monthly_payment.quantize(Decimal("0.01"))

    def calculate_financing_plan(
        self,
        car_price: Decimal,
        down_payment: Decimal,
        years: int,
        interest_rate: Optional[Decimal] = None
    ) -> FinancingPlan:
        """Calculate a financing plan for the given years"""
        if interest_rate is None:
            interest_rate = self.interest_rate

        # Validate years
        if years not in [3, 4, 5, 6]:
            raise ValueError("El plazo debe ser 3, 4, 5 o 6 años")

        # Financed amount
        financed_amount = car_price - down_payment

        if financed_amount <= 0:
            raise ValueError("El enganche no puede ser mayor o igual al precio del vehículo")

        # Convert years to months
        months = years * 12

        # Calculate monthly payment
        monthly_payment = self.calculate_monthly_payment(
            financed_amount,
            interest_rate,
            months
        )

        total_amount = monthly_payment * Decimal(str(months))
        interest_amount = total_amount - financed_amount

        return FinancingPlan(
            years=years,
            months=months,
            monthly_payment=monthly_payment,
            total_amount=total_amount.quantize(Decimal("0.01")),
            interest_amount=interest_amount.quantize(Decimal("0.01"))
        )
