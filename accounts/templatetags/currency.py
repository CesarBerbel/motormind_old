from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="brl")
def brl(value):
    """
    Format a numeric value as Brazilian Real currency.
    """
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        decimal_value = Decimal("0.00")

    formatted_value = f"{decimal_value:,.2f}"
    formatted_value = (
        formatted_value.replace(",", "X").replace(".", ",").replace("X", ".")
    )

    return f"R$ {formatted_value}"
