"""Tests for FinancingService"""
import pytest
from decimal import Decimal
from src.services.financing_service import FinancingService


class TestCalculateMonthlyPayment:
    """Tests for calculate_monthly_payment method"""

    def test_calculate_monthly_payment_basic(self):
        """Test basic monthly payment calculation"""
        service = FinancingService()
        principal = Decimal("100000")
        annual_rate = Decimal("0.10")  # 10%
        months = 36

        payment = service.calculate_monthly_payment(principal, annual_rate, months)

        assert payment > 0
        assert payment < principal  # Payment should be less than principal
        # Approximate check: should be around 3226 for 100k at 10% for 36 months
        assert 3000 < float(payment) < 3500

    def test_calculate_monthly_payment_zero_interest(self):
        """Test calculation with zero interest rate"""
        service = FinancingService()
        principal = Decimal("100000")
        annual_rate = Decimal("0")
        months = 36

        payment = service.calculate_monthly_payment(principal, annual_rate, months)

        # With 0% interest, payment should be principal / months
        expected = principal / Decimal(str(months))
        assert abs(payment - expected) < Decimal("0.01")

    def test_calculate_monthly_payment_zero_principal(self):
        """Test calculation with zero principal"""
        service = FinancingService()
        principal = Decimal("0")
        annual_rate = Decimal("0.10")
        months = 36

        payment = service.calculate_monthly_payment(principal, annual_rate, months)

        assert payment == Decimal("0")

    def test_calculate_monthly_payment_zero_months(self):
        """Test calculation with zero months"""
        service = FinancingService()
        principal = Decimal("100000")
        annual_rate = Decimal("0.10")
        months = 0

        payment = service.calculate_monthly_payment(principal, annual_rate, months)

        assert payment == Decimal("0")

    def test_calculate_monthly_payment_negative_principal(self):
        """Test calculation with negative principal"""
        service = FinancingService()
        principal = Decimal("-100000")
        annual_rate = Decimal("0.10")
        months = 36

        payment = service.calculate_monthly_payment(principal, annual_rate, months)

        assert payment == Decimal("0")


class TestCalculateFinancingPlan:
    """Tests for calculate_financing_plan method"""

    def test_calculate_financing_plan_3_years(self):
        """Test financing plan for 3 years"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=3)

        assert plan.years == 3
        assert plan.months == 36
        assert plan.monthly_payment > 0
        assert plan.total_amount > plan.monthly_payment * Decimal("35")  # Should be close to 36 payments
        assert plan.interest_amount > 0

    def test_calculate_financing_plan_4_years(self):
        """Test financing plan for 4 years"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=4)

        assert plan.years == 4
        assert plan.months == 48
        assert plan.monthly_payment > 0
        # Monthly payment should be less than 3-year plan
        plan_3y = service.calculate_financing_plan(car_price, down_payment, years=3)
        assert plan.monthly_payment < plan_3y.monthly_payment

    def test_calculate_financing_plan_5_years(self):
        """Test financing plan for 5 years"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=5)

        assert plan.years == 5
        assert plan.months == 60
        assert plan.monthly_payment > 0

    def test_calculate_financing_plan_6_years(self):
        """Test financing plan for 6 years"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=6)

        assert plan.years == 6
        assert plan.months == 72
        assert plan.monthly_payment > 0

    def test_calculate_financing_plan_invalid_years(self):
        """Test financing plan with invalid years"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        with pytest.raises(ValueError, match="El plazo debe ser 3, 4, 5 o 6 años"):
            service.calculate_financing_plan(car_price, down_payment, years=2)

        with pytest.raises(ValueError, match="El plazo debe ser 3, 4, 5 o 6 años"):
            service.calculate_financing_plan(car_price, down_payment, years=7)

        with pytest.raises(ValueError, match="El plazo debe ser 3, 4, 5 o 6 años"):
            service.calculate_financing_plan(car_price, down_payment, years=1)

    def test_calculate_financing_plan_down_payment_too_high(self):
        """Test financing plan with down payment >= car price"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("200000")

        with pytest.raises(ValueError, match="El enganche no puede ser mayor o igual al precio"):
            service.calculate_financing_plan(car_price, down_payment, years=3)

        down_payment = Decimal("250000")
        with pytest.raises(ValueError, match="El enganche no puede ser mayor o igual al precio"):
            service.calculate_financing_plan(car_price, down_payment, years=3)

    def test_calculate_financing_plan_custom_interest_rate(self):
        """Test financing plan with custom interest rate"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")
        custom_rate = Decimal("0.15")  # 15%

        plan = service.calculate_financing_plan(
            car_price, down_payment, years=3, interest_rate=custom_rate
        )

        assert plan.monthly_payment > 0
        # Higher interest rate should result in higher monthly payment
        plan_default = service.calculate_financing_plan(car_price, down_payment, years=3)
        assert plan.monthly_payment > plan_default.monthly_payment

    def test_calculate_financing_plan_total_amount(self):
        """Test that total amount equals monthly payment * months"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=3)

        expected_total = plan.monthly_payment * Decimal(str(plan.months))
        # Allow small rounding differences
        assert abs(plan.total_amount - expected_total) < Decimal("1.00")

    def test_calculate_financing_plan_interest_amount(self):
        """Test that interest amount is calculated correctly"""
        service = FinancingService()
        car_price = Decimal("200000")
        down_payment = Decimal("40000")
        financed_amount = car_price - down_payment

        plan = service.calculate_financing_plan(car_price, down_payment, years=3)

        # Interest amount should be total - financed amount
        expected_interest = plan.total_amount - financed_amount
        assert abs(plan.interest_amount - expected_interest) < Decimal("0.01")

    def test_calculate_financing_plan_edge_case_small_amount(self):
        """Test financing plan with very small amounts"""
        service = FinancingService()
        car_price = Decimal("10000")
        down_payment = Decimal("2000")
        financed_amount = car_price - down_payment

        plan = service.calculate_financing_plan(car_price, down_payment, years=3)

        assert plan.monthly_payment > 0
        assert plan.total_amount > financed_amount

    def test_calculate_financing_plan_edge_case_large_amount(self):
        """Test financing plan with very large amounts"""
        service = FinancingService()
        car_price = Decimal("1000000")
        down_payment = Decimal("200000")

        plan = service.calculate_financing_plan(car_price, down_payment, years=3)

        assert plan.monthly_payment > 0
        assert plan.total_amount > car_price - down_payment
