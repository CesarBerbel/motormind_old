from decimal import Decimal

from django.db.models import Case, CharField, DecimalField, F, Value, When

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


def get_parts_with_stock_logic_queryset():
    """
    Return a queryset annotated with stock priority and purchase suggestions.
    This moves the logic from Python memory to the database (SQL).
    """
    return Part.objects.filter(is_active=True).annotate(
        # Calculate current stock ratio relative to minimum stock
        # To avoid division by zero, we treat 0 as a very small value or handle it via Case
        restock_priority_level=Case(
            When(current_stock__lte=0, then=Value("critical")),
            When(
                current_stock__lte=F("minimum_stock") * Decimal("0.5"),
                then=Value("critical"),
            ),
            When(
                current_stock__lte=F("minimum_stock") * Decimal("0.75"),
                then=Value("high"),
            ),
            When(current_stock__lte=F("minimum_stock"), then=Value("medium")),
            default=Value("normal"),
            output_field=CharField(),
        ),
        # Suggestion: (Minimum * 2) - Current Stock, if below minimum.
        purchase_suggestion_qty=Case(
            When(
                current_stock__lt=F("minimum_stock"),
                then=(F("minimum_stock") * 2) - F("current_stock"),
            ),
            default=Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        ),
    )
