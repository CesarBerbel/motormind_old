from django import template

register = template.Library()


@register.filter
def brl(value):
    """
    Format value as Brazilian Real currency.
    """
    try:
        value = float(value)
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (TypeError, ValueError):
        return "R$ 0,00"
