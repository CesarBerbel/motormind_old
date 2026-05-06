from decimal import Decimal

from django.db.models import (
    Case,
    CharField,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from inventory.models import Part, PurchaseOrder, ServiceOrderPart, StockMovement


def get_active_parts():
    """
    Retorna peças ativas ordenadas por nome.
    """
    return Part.objects.filter(
        is_active=True,
    ).order_by(
        "name",
    )


def get_low_stock_parts():
    """
    Retorna peças ativas com estoque atual menor ou igual ao estoque mínimo.
    """
    return get_active_parts().filter(
        current_stock__lte=F("minimum_stock"),
    )


def count_low_stock_parts():
    """
    Conta peças ativas em estoque baixo.
    """
    return get_low_stock_parts().count()


def get_restock_priority(part):
    """
    Calcula prioridade de reposição de uma peça.
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

    if part.current_stock < (part.minimum_stock / Decimal("2")):
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
    Sugere compra suficiente para chegar a 2x o estoque mínimo.
    """
    if part.minimum_stock <= 0:
        return Decimal("0.00")

    target_stock = part.minimum_stock * Decimal("2")
    suggestion = target_stock - part.current_stock

    if suggestion <= 0:
        return Decimal("0.00")

    return suggestion


def get_critical_parts_with_priority():
    """
    Retorna peças críticas com prioridade e sugestão de compra.
    """
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
    """
    Queryset de peças ativas com prioridade e sugestão de compra anotadas.
    """
    return Part.objects.filter(
        is_active=True,
    ).annotate(
        restock_priority_level=Case(
            When(
                current_stock__lte=0,
                then=Value("critical"),
            ),
            When(
                current_stock__lt=F("minimum_stock") * Decimal("0.50"),
                then=Value("critical"),
            ),
            When(
                current_stock__lt=F("minimum_stock"),
                then=Value("high"),
            ),
            When(
                current_stock=F("minimum_stock"),
                then=Value("medium"),
            ),
            default=Value("normal"),
            output_field=CharField(),
        ),
        purchase_suggestion_qty=Case(
            When(
                current_stock__lt=F("minimum_stock"),
                then=(F("minimum_stock") * Decimal("2")) - F("current_stock"),
            ),
            default=Value(Decimal("0.00")),
            output_field=DecimalField(
                max_digits=10,
                decimal_places=2,
            ),
        ),
    )


def get_billable_parts_for_service_order(order_id):
    """
    Retorna peças cobradas na ordem.

    A regra atual considera como cobraveis:
    - reservadas;
    - aguardando compra;
    - usadas.
    """
    return (
        ServiceOrderPart.objects.select_related(
            "part",
            "service_order",
        )
        .filter(
            service_order_id=order_id,
            status__in=[
                ServiceOrderPart.Status.RESERVED,
                ServiceOrderPart.Status.WAITING_PURCHASE,
                ServiceOrderPart.Status.USED,
            ],
        )
        .order_by(
            "created_at",
        )
    )


def get_parts_total_for_service_order(order_id):
    """
    Retorna total cobravel de peças de uma OS.
    """
    total = get_billable_parts_for_service_order(
        order_id,
    ).aggregate(
        total=Coalesce(
            Sum(
                F("quantity") * F("unit_price") - F("discount"),
            ),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        )
    )["total"]

    if total < Decimal("0.00"):
        return Decimal("0.00")

    return total


def count_billable_parts_for_service_order(order_id):
    """
    Conta peças cobraveis da OS.
    """
    return get_billable_parts_for_service_order(
        order_id,
    ).count()


def get_restock_suggestions():
    """
    Retorna sugestões de reposição para peças em baixo estoque.
    """
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


def get_inventory_dashboard_data():
    """
    Monta o contexto completo do dashboard de estoque.

    O dashboard é somente leitura.
    Os cálculos ficam no selector para evitar regra de negócio dentro do template.
    """
    parts = Part.objects.select_related(
        "brand",
        "category",
    )

    active_parts = parts.filter(
        is_active=True,
    )

    low_stock_rows = get_critical_parts_with_priority()

    stock_totals = active_parts.aggregate(
        total_parts=Count("id"),
        total_stock_quantity=Coalesce(
            Sum("current_stock"),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        ),
        stock_cost_value=Coalesce(
            Sum(
                F("current_stock") * F("cost_price"),
            ),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        ),
        stock_sale_value=Coalesce(
            Sum(
                F("current_stock") * F("sale_price"),
            ),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        ),
    )

    purchase_order_counts = PurchaseOrder.objects.aggregate(
        open_count=Count(
            "id",
            filter=Q(
                status=PurchaseOrder.Status.OPEN,
            ),
        ),
        ordered_count=Count(
            "id",
            filter=Q(
                status=PurchaseOrder.Status.ORDERED,
            ),
        ),
        received_count=Count(
            "id",
            filter=Q(
                status=PurchaseOrder.Status.RECEIVED,
            ),
        ),
        canceled_count=Count(
            "id",
            filter=Q(
                status=PurchaseOrder.Status.CANCELED,
            ),
        ),
        pending_quantity=Coalesce(
            Sum(
                "requested_quantity",
                filter=Q(
                    status__in=[
                        PurchaseOrder.Status.OPEN,
                        PurchaseOrder.Status.ORDERED,
                    ],
                ),
            ),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        ),
    )

    service_order_part_counts = ServiceOrderPart.objects.aggregate(
        reserved_count=Count(
            "id",
            filter=Q(
                status=ServiceOrderPart.Status.RESERVED,
            ),
        ),
        waiting_purchase_count=Count(
            "id",
            filter=Q(
                status=ServiceOrderPart.Status.WAITING_PURCHASE,
            ),
        ),
        used_count=Count(
            "id",
            filter=Q(
                status=ServiceOrderPart.Status.USED,
            ),
        ),
        pending_purchase_quantity=Coalesce(
            Sum(
                F("quantity") - F("reserved_quantity"),
                filter=Q(
                    status=ServiceOrderPart.Status.WAITING_PURCHASE,
                ),
            ),
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        ),
    )

    movement_counts = StockMovement.objects.aggregate(
        entries_count=Count(
            "id",
            filter=Q(
                movement_type=StockMovement.MovementType.IN,
            ),
        ),
        exits_count=Count(
            "id",
            filter=Q(
                movement_type__in=[
                    StockMovement.MovementType.OUT,
                    StockMovement.MovementType.RESERVE,
                    StockMovement.MovementType.LOSS,
                ],
            ),
        ),
        returns_count=Count(
            "id",
            filter=Q(
                movement_type__in=[
                    StockMovement.MovementType.RETURN,
                    StockMovement.MovementType.RELEASE,
                ],
            ),
        ),
        adjustments_count=Count(
            "id",
            filter=Q(
                movement_type=StockMovement.MovementType.ADJUST,
            ),
        ),
    )

    category_rows = (
        active_parts.values(
            "category__name",
        )
        .annotate(
            parts_count=Count("id"),
            low_stock_count=Count(
                "id",
                filter=Q(
                    current_stock__lte=F("minimum_stock"),
                ),
            ),
            stock_quantity=Coalesce(
                Sum("current_stock"),
                Decimal("0.00"),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2,
                ),
            ),
            stock_sale_value=Coalesce(
                Sum(
                    F("current_stock") * F("sale_price"),
                ),
                Decimal("0.00"),
                output_field=DecimalField(
                    max_digits=14,
                    decimal_places=2,
                ),
            ),
        )
        .order_by(
            "category__name",
        )
    )

    recent_movements = StockMovement.objects.select_related(
        "part",
        "created_by",
        "service_order",
    ).order_by("-created_at",)[:10]

    recent_purchase_orders = PurchaseOrder.objects.select_related(
        "part",
        "service_order",
        "service_order__customer",
        "created_by",
    ).order_by("-created_at",)[:8]

    return {
        "stock_totals": stock_totals,
        "inactive_parts_count": parts.filter(
            is_active=False,
        ).count(),
        "low_stock_count": len(low_stock_rows),
        "critical_parts": low_stock_rows[:8],
        "purchase_order_counts": purchase_order_counts,
        "service_order_part_counts": service_order_part_counts,
        "movement_counts": movement_counts,
        "category_rows": category_rows,
        "recent_movements": recent_movements,
        "recent_purchase_orders": recent_purchase_orders,
    }
