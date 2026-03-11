"""
apps/common/utils/currency.py  — Currency conversion helpers.
"""

from decimal import Decimal


def convert_amount(amount: Decimal, from_currency: str, to_currency: str, rate: Decimal) -> Decimal:
    """
    Convert *amount* from *from_currency* to *to_currency* using *rate*.
    rate = how many to_currency units equal 1 from_currency unit.
    """
    if from_currency == to_currency:
        return amount
    return (amount * rate).quantize(Decimal("0.01"))
