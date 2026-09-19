from decimal import Decimal


def apply_discount(subtotal: Decimal, percent: Decimal) -> Decimal:
    """Return subtotal after a percentage discount."""
    return subtotal * (Decimal("1") - percent / Decimal("100"))
