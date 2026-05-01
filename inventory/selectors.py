from inventory.models import Part


def get_active_parts():
    """
    Return active inventory parts.
    """
    return Part.objects.filter(
        is_active=True,
    ).order_by(
        "name",
    )


def get_low_stock_parts():
    """
    Return active parts with current stock less than or equal to minimum stock.
    """
    return [part for part in get_active_parts() if part.is_low_stock]


def count_low_stock_parts():
    """
    Count active parts with low stock.
    """
    return len(get_low_stock_parts())
