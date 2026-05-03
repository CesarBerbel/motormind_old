from decimal import Decimal

from django.db.models import Case, CharField, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce

from inventory.models import Part, ServiceOrderPart


def get_active_parts():
    return Part.objects.filter(is_active=True).order_by("name")


def get_low_stock_parts():
    return get_active_parts().filter(current_stock__lte=F("minimum_stock"))


def count_low_stock_parts():
    return get_low_stock_parts().count()


def get_restock_priority(part):
    if part.minimum_stock <= 0:
        return {"level": "normal", "label": "Normal", "css_class": "success"}

    if part.current_stock <= 0:
        return {"level": "critical", "label": "Crítica", "css_class": "danger"}

    if part.current_stock < (part.minimum_stock / Decimal("2")):
        return {"level": "critical", "label": "Crítica", "css_class": "danger"}

    if part.current_stock < part.minimum_stock:
        return {"level": "high", "label": "Alta", "css_class": "warning"}

    if part.current_stock == part.minimum_stock:
        return {"level": "medium", "label": "Média", "css_class": "info"}

    return {"level": "normal", "label": "Normal", "css_class": "success"}


def get_restock_suggestion_quantity(part):
    if part.minimum_stock <= 0:
        return Decimal("0.00")

    target_stock = part.minimum_stock * Decimal("2")
    suggestion = target_stock - part.current_stock

    if suggestion <= 0:
        return Decimal("0.00")

    return suggestion


def get_critical_parts_with_priority():
    rows = []

    for part in get_low_stock_parts():
        rows.append(
            {
                "part": part,
                "priority": get_restock_priority(part),
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
        rows,
        key=lambda row: (
            priority_order[row["priority"]["level"]],
            row["part"].current_stock,
            row["part"].name,
        ),
    )


def get_parts_with_stock_logic_queryset():
    return Part.objects.filter(is_active=True).annotate(
        restock_priority_level=Case(
            When(current_stock__lte=0, then=Value("critical")),
            When(
                current_stock__lt=F("minimum_stock") * Decimal("0.50"),
                then=Value("critical"),
            ),
            When(current_stock__lt=F("minimum_stock"), then=Value("high")),
            When(current_stock=F("minimum_stock"), then=Value("medium")),
            default=Value("normal"),
            output_field=CharField(),
        ),
        purchase_suggestion_qty=Case(
            When(
                current_stock__lt=F("minimum_stock"),
                then=(F("minimum_stock") * Decimal("2")) - F("current_stock"),
            ),
            default=Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        ),
    )


def get_billable_parts_for_service_order(order_id):
    return (
        ServiceOrderPart.objects.select_related("part", "service_order")
        .filter(
            service_order_id=order_id,
            status__in=[
                ServiceOrderPart.Status.RESERVED,
                ServiceOrderPart.Status.USED,
            ],
        )
        .order_by("created_at")
    )


def get_parts_total_for_service_order(order_id):
    total = get_billable_parts_for_service_order(order_id).aggregate(
        total=Coalesce(
            Sum(F("quantity") * F("unit_price") - F("discount")),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )["total"]

    if total < Decimal("0.00"):
        return Decimal("0.00")

    return total


def count_billable_parts_for_service_order(order_id):
    return get_billable_parts_for_service_order(order_id).count()


def get_restock_suggestions():
    suggestions = []

    for part in get_low_stock_parts():
        suggestions.append(
            {
                "part": part,
                "priority": get_restock_priority(part),
                "suggestion_quantity": get_restock_suggestion_quantity(part),
            }
        )

    return suggestions
