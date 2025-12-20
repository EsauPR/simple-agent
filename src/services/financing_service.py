from decimal import Decimal
from typing import List, Optional
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
        """Calcula el pago mensual usando la fórmula de interés compuesto"""
        if principal <= 0:
            return Decimal("0")

        if months <= 0:
            return Decimal("0")

        # Tasa mensual
        monthly_rate = annual_rate / Decimal("12")

        # Si la tasa es 0, simplemente dividir principal entre meses
        if monthly_rate == 0:
            return principal / Decimal(str(months))

        # Fórmula: P = (P * r * (1 + r)^n) / ((1 + r)^n - 1)
        # Donde P = principal, r = tasa mensual, n = número de meses

        one_plus_rate = Decimal("1") + monthly_rate
        one_plus_rate_power = Decimal(str(pow(float(one_plus_rate), months)))

        numerator = principal * monthly_rate * one_plus_rate_power
        denominator = one_plus_rate_power - Decimal("1")

        if denominator == 0:
            return principal / Decimal(str(months))

        monthly_payment = numerator / denominator

        return monthly_payment.quantize(Decimal("0.01"))

    def calculate_financing_plans(
        self,
        car_price: Decimal,
        down_payment: Decimal,
        interest_rate: Optional[Decimal] = None,
        min_months: int = 36,
        max_months: int = 72
    ) -> List[FinancingPlan]:
        """Calcula planes de financiamiento para diferentes plazos"""
        if interest_rate is None:
            interest_rate = self.interest_rate

        # Monto financiado
        financed_amount = car_price - down_payment

        if financed_amount <= 0:
            return []

        plans = []

        # Plazos estándar: 36, 48, 60, 72 meses (3, 4, 5, 6 años)
        available_months = [36, 48, 60, 72]

        # Filtrar por min y max
        available_months = [m for m in available_months if min_months <= m <= max_months]

        for months in available_months:
            monthly_payment = self.calculate_monthly_payment(
                financed_amount,
                interest_rate,
                months
            )

            total_amount = monthly_payment * Decimal(str(months))
            interest_amount = total_amount - financed_amount

            plans.append(FinancingPlan(
                months=months,
                monthly_payment=monthly_payment,
                total_amount=total_amount.quantize(Decimal("0.01")),
                interest_amount=interest_amount.quantize(Decimal("0.01"))
            ))

        return plans

    def get_default_down_payment(self, car_price: Decimal) -> Decimal:
        """Calcula el enganche por defecto (10% del precio)"""
        return (car_price * self.default_down_payment_percent).quantize(Decimal("0.01"))
