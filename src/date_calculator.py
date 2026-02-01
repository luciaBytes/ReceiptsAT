"""
Rent period calculator for tax-compliant date calculations.

This is a tax-critical module - all date arithmetic must be auditable and correct.
Every calculation provides an explanation for audit trail purposes.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Tuple

try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for when imported directly
    from .utils.logger import get_logger

logger = get_logger(__name__)


class RentPeriodCalculator:
    """
    Calculate rent periods from payment information.
    
    This calculator handles the complex business logic of determining which
    rent period a payment covers based on:
    - When the payment was made
    - How many months in advance tenants typically pay (rent_deposit)
    - How many months late the tenant is
    - Whether the payment is for the current month (override flag)
    
    All calculations are auditable via the explain() method.
    """
    
    def __init__(self, payment_date: date, rent_deposit: int, 
                 months_late: int, paid_current_month: bool):
        """
        Initialize calculator with payment parameters.
        
        Args:
            payment_date: Date payment was made
            rent_deposit: Months paid in advance (typically 1)
                         e.g., 1 means paying for next month
            months_late: Months behind on payment (0 if on time)
            paid_current_month: True if paying for current month instead of future
        
        Raises:
            ValueError: If inputs are invalid
        
        Example:
            # Payment on Jan 5, typically pays 1 month ahead, on time
            calc = RentPeriodCalculator(date(2026, 1, 5), 1, 0, False)
            from_date, to_date = calc.calculate()
            # Result: Feb 1 to Feb 28 (paying for February)
        """
        self._validate_inputs(payment_date, rent_deposit, months_late)
        
        self.payment_date = payment_date
        self.rent_deposit = rent_deposit
        self.months_late = months_late
        self.paid_current_month = paid_current_month
        
        logger.debug(
            f"RentPeriodCalculator initialized: "
            f"payment_date={payment_date}, rent_deposit={rent_deposit}, "
            f"months_late={months_late}, paid_current_month={paid_current_month}"
        )
    
    def _validate_inputs(self, payment_date: date, rent_deposit: int, 
                        months_late: int) -> None:
        """
        Validate constructor inputs.
        
        Args:
            payment_date: Date to validate
            rent_deposit: Rent deposit months to validate
            months_late: Months late to validate
        
        Raises:
            ValueError: If any input is invalid
        """
        if not isinstance(payment_date, date):
            raise ValueError(
                f"payment_date must be a date object, got {type(payment_date).__name__}"
            )
        
        if not isinstance(rent_deposit, int):
            raise ValueError(
                f"rent_deposit must be an integer, got {type(rent_deposit).__name__}"
            )
        
        if rent_deposit < 0:
            raise ValueError(
                f"rent_deposit cannot be negative, got {rent_deposit}"
            )
        
        if not isinstance(months_late, int):
            raise ValueError(
                f"months_late must be an integer, got {type(months_late).__name__}"
            )
        
        if months_late < 0:
            raise ValueError(
                f"months_late cannot be negative, got {months_late}"
            )
    
    def calculate(self) -> Tuple[date, date]:
        """
        Calculate rent period from/to dates.
        
        Logic:
        - If paid_current_month is True: rent period = payment month
        - Otherwise: rent period = payment_date + rent_deposit months - months_late months
        
        Returns:
            Tuple of (from_date, to_date) for the rent period
            - from_date: First day of the rent period month
            - to_date: Last day of the rent period month (handles month length variations)
        
        Example:
            # Payment on Jan 5, rent_deposit=1, months_late=0
            # Result: Feb 1 to Feb 28/29
            
            # Payment on Mar 15, rent_deposit=1, months_late=2
            # Result: Dec 1 to Dec 31 (paying late for December)
        """
        if self.paid_current_month:
            # Override: paying for current month regardless of normal calculation
            target_month = self.payment_date
            logger.debug(
                f"PaidCurrentMonth flag set - using payment month directly: "
                f"{target_month.strftime('%Y-%m')}"
            )
        else:
            # Normal calculation: payment_date + rent_deposit - months_late
            offset_months = self.rent_deposit - self.months_late
            target_month = self.payment_date + relativedelta(months=offset_months)
            logger.debug(
                f"Calculating target month: {self.payment_date.strftime('%Y-%m-%d')} "
                f"+ {self.rent_deposit} months - {self.months_late} months "
                f"= {target_month.strftime('%Y-%m-%d')} (offset: {offset_months})"
            )
        
        # Get first day of target month
        from_date = target_month.replace(day=1)
        
        # Get last day of target month
        # Calculate as: first day of next month - 1 day
        # This correctly handles varying month lengths (28/29/30/31 days)
        next_month = from_date + relativedelta(months=1)
        to_date = next_month - relativedelta(days=1)
        
        logger.debug(
            f"Calculated rent period: {from_date.strftime('%Y-%m-%d')} "
            f"to {to_date.strftime('%Y-%m-%d')}"
        )
        
        return (from_date, to_date)
    
    def explain(self) -> str:
        """
        Generate human-readable explanation of calculation.
        
        This method is critical for audit trails and tax compliance.
        It provides a clear, readable explanation of how the rent period
        was calculated from the input parameters.
        
        Returns:
            Explanation string suitable for logging and reporting
        
        Example output:
            "Payment on 2026-01-05 + 1 months - 0 months (offset: 1) 
             → Period: 2026-02-01 to 2026-02-28"
        """
        from_date, to_date = self.calculate()
        
        if self.paid_current_month:
            return (
                f"Payment on {self.payment_date.strftime('%Y-%m-%d')} "
                f"for current month (PaidCurrentMonth flag set) "
                f"→ Period: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
            )
        
        offset = self.rent_deposit - self.months_late
        
        return (
            f"Payment on {self.payment_date.strftime('%Y-%m-%d')} "
            f"+ {self.rent_deposit} months - {self.months_late} months "
            f"(offset: {offset}) "
            f"→ Period: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        )


def calculate_rent_period(payment_date: date, rent_deposit: int,
                         months_late: int, paid_current_month: bool) -> Tuple[date, date]:
    """
    Convenience function for one-off rent period calculations.
    
    For repeated calculations, use RentPeriodCalculator directly for better performance.
    
    Args:
        payment_date: Date payment was made
        rent_deposit: Months paid in advance
        months_late: Months behind on payment
        paid_current_month: True if paying for current month
    
    Returns:
        Tuple of (from_date, to_date) for the rent period
    
    Raises:
        ValueError: If inputs are invalid
    """
    calculator = RentPeriodCalculator(payment_date, rent_deposit, months_late, paid_current_month)
    return calculator.calculate()
