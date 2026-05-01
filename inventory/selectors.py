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


def get_restock_priority(part):
    """
    Return restock priority based on current stock and minimum stock.

    Critical:
    - current stock is zero
    - or current stock is less than 50% of minimum stock

    High:
    - current stock is below minimum stock

    Medium:
    - current stock is equal to minimum stock

    Normal:
    - current stock is above minimum stock
    """
    if part.minimum_stock <= 0:
        return {
            "level": "normal",
            "label": "Normal",
            "css_class": "success",
        }

    if part.current_stock <= 0:
        return {
            "level": "critical",
            "label": "Crítica",
            "css_class": "danger",
        }

    if part.current_stock < (part.minimum_stock / 2):
        return {
            "level": "critical",
            "label": "Crítica",
            "css_class": "danger",
        }

    if part.current_stock < part.minimum_stock:
        return {
            "level": "high",
            "label": "Alta",
            "css_class": "warning",
        }

    if part.current_stock == part.minimum_stock:
        return {
            "level": "medium",
            "label": "Média",
            "css_class": "info",
        }

    return {
        "level": "normal",
        "label": "Normal",
        "css_class": "success",
    }


def get_restock_suggestion_quantity(part):
    """
    Return suggested quantity to buy.

    Suggestion rule:
    - buy enough to reach twice the minimum stock
    - if minimum stock is zero, suggest zero
    """
    if part.minimum_stock <= 0:
        return 0

    target_stock = part.minimum_stock * 2
    suggestion = target_stock - part.current_stock

    if suggestion <= 0:
        return 0

    return suggestion


def get_critical_parts_with_priority():
    """
    Return low stock parts enriched with restock priority information.
    """
    critical_parts = []

    for part in get_low_stock_parts():
        priority = get_restock_priority(part)

        critical_parts.append(
            {
                "part": part,
                "priority": priority,
                "suggestion_quantity": get_restock_suggestion_quantity(part),
            }
        )

    priority_order = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "normal": 4,
    }

    return sorted(
        critical_parts,
        key=lambda row: (
            priority_order[row["priority"]["level"]],
            row["part"].current_stock,
            row["part"].name,
        ),
    )
