from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


def get_mechanic_queryset():
    """
    Return active users from mechanic group.
    """
    User = get_user_model()

    mechanic_group = Group.objects.filter(name="Mecânico").first()

    if not mechanic_group:
        return User.objects.none()

    return User.objects.filter(
        groups=mechanic_group,
        is_active=True,
    ).order_by(
        "first_name",
        "email",
    )


def get_priority_ordering_annotation():
    """
    Return priority ordering annotation.

    High priority comes first, then medium, then low.
    """
    return Case(
        When(priority=ServiceOrder.Priority.HIGH, then=Value(1)),
        When(priority=ServiceOrder.Priority.MEDIUM, then=Value(2)),
        When(priority=ServiceOrder.Priority.LOW, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )


def get_overdue_service_order_filter():
    """
    Return filter for overdue active service orders.
    """
    today = timezone.localdate()

    return Q(expected_delivery_date__lt=today) & ~Q(
        status__in=[
            ServiceOrder.Status.FINISHED,
            ServiceOrder.Status.CANCELED,
        ]
    )


def get_service_orders_base_queryset():
    """
    Return base queryset for service orders with common relationships.
    """
    return ServiceOrder.objects.select_related(
        "customer",
        "vehicle",
        "created_by",
        "assigned_mechanic",
    ).annotate(
        priority_order=get_priority_ordering_annotation(),
    )


def get_service_orders_for_list():
    """
    Return ordered queryset for service order list.
    """
    return get_service_orders_base_queryset().order_by(
        "priority_order",
        "expected_delivery_date",
        "-created_at",
    )


def get_service_orders_for_board():
    """
    Return ordered queryset for operational board.
    """
    return get_service_orders_base_queryset().order_by(
        "priority_order",
        "expected_delivery_date",
        "created_at",
    )


def filter_service_orders_by_search(queryset, search):
    """
    Apply common service order search filter.
    """
    if not search:
        return queryset

    return queryset.filter(
        Q(customer__name__icontains=search)
        | Q(vehicle__plate__icontains=search)
        | Q(vehicle__brand__icontains=search)
        | Q(vehicle__model__icontains=search)
        | Q(title__icontains=search)
        | Q(description__icontains=search)
        | Q(assigned_mechanic__email__icontains=search)
        | Q(assigned_mechanic__first_name__icontains=search)
        | Q(assigned_mechanic__last_name__icontains=search)
    )


def get_board_status_columns(service_orders):
    """
    Group service orders by status for operational board.
    """
    status_columns = []

    for status_value, status_label in ServiceOrder.Status.choices:
        status_columns.append(
            {
                "value": status_value,
                "label": status_label,
                "orders": service_orders.filter(status=status_value),
            }
        )

    return status_columns


def get_agenda_service_orders(start_date, end_date):
    """
    Return service orders scheduled by expected delivery date.
    """
    return (
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
            "assigned_mechanic",
        )
        .annotate(
            priority_order=get_priority_ordering_annotation(),
        )
        .filter(
            expected_delivery_date__gte=start_date,
            expected_delivery_date__lte=end_date,
        )
        .exclude(
            status=ServiceOrder.Status.CANCELED,
        )
        .order_by(
            "expected_delivery_date",
            "priority_order",
            "created_at",
        )
    )


def get_closed_time_entries_for_period(start_datetime, end_datetime):
    """
    Return closed time entries inside a period.
    """
    return (
        ServiceOrderTimeEntry.objects.select_related(
            "mechanic",
            "service_order",
            "service_order__customer",
            "service_order__vehicle",
        )
        .filter(
            started_at__gte=start_datetime,
            started_at__lte=end_datetime,
            ended_at__isnull=False,
        )
        .order_by(
            "mechanic__email",
            "-started_at",
        )
    )


def get_active_service_orders_for_mechanic(mechanic):
    """
    Return active service orders assigned to the given mechanic.
    """
    return (
        get_service_orders_base_queryset()
        .filter(
            assigned_mechanic=mechanic,
        )
        .exclude(
            status__in=[
                ServiceOrder.Status.FINISHED,
                ServiceOrder.Status.CANCELED,
            ]
        )
        .order_by(
            "priority_order",
            "expected_delivery_date",
            "created_at",
        )
    )


def get_overdue_service_orders_for_mechanic(mechanic):
    """
    Return overdue active service orders assigned to the given mechanic.
    """
    return get_active_service_orders_for_mechanic(mechanic).filter(
        get_overdue_service_order_filter()
    )


def get_open_time_entry_for_mechanic(mechanic):
    """
    Return the current open time entry for the given mechanic, if any.
    """
    return (
        ServiceOrderTimeEntry.objects.select_related(
            "service_order",
            "service_order__customer",
            "service_order__vehicle",
        )
        .filter(
            mechanic=mechanic,
            ended_at__isnull=True,
        )
        .order_by(
            "-started_at",
        )
        .first()
    )


def get_billable_inventory_parts(service_order):
    """
    Return inventory parts that must be included in service order financial total.
    """
    return service_order.inventory_parts.select_related(
        "part",
        "created_by",
    ).filter(
        status__in=[
            "reserved",
            "used",
        ]
    )


def get_all_inventory_parts_for_service_order(service_order):
    """
    Return all inventory parts linked to a service order.
    """
    return service_order.inventory_parts.select_related(
        "part",
        "created_by",
    ).all()


def calculate_inventory_parts_total(service_order):
    """
    Calculate total amount of billable inventory parts.
    """
    total = Decimal("0.00")

    for inventory_part in get_billable_inventory_parts(service_order):
        total += inventory_part.total

    return total


def money(value):
    """Normalize monetary values to the database scale used by DecimalField.

    Multiplying DecimalField values such as Decimal("1.00") * Decimal("100.00")
    can produce Decimal("100.0000"). Django validates decimal_places before
    saving financial models, so all public financial totals must be quantized
    to exactly two decimal places.
    """
    if value is None:
        value = Decimal("0.00")
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_service_order_financial_summary(service_order):
    """
    Return the single financial summary contract for a service order.

    All templates and financial services must use this selector instead of
    recalculating totals independently.
    """
    from service_orders.models import ServiceOrderItem

    manual_services_total = Decimal("0.00")
    manual_parts_total = Decimal("0.00")

    for item in service_order.items.all():
        if item.item_type == ServiceOrderItem.ItemType.SERVICE:
            manual_services_total += item.total
        elif item.item_type == ServiceOrderItem.ItemType.PART:
            manual_parts_total += item.total

    manual_services_total = money(manual_services_total)
    manual_parts_total = money(manual_parts_total)
    manual_items_total = money(manual_services_total + manual_parts_total)
    inventory_parts_total = money(calculate_inventory_parts_total(service_order))
    labor_cost = money(service_order.labor_cost)
    extra_parts_cost = money(service_order.parts_cost)
    discount = money(service_order.discount)

    gross_total = money(
        manual_services_total
        + manual_parts_total
        + inventory_parts_total
        + labor_cost
        + extra_parts_cost
    )
    net_total = money(gross_total - discount)

    if net_total < Decimal("0.00"):
        net_total = Decimal("0.00")

    return {
        "order_id": service_order.pk,
        "manual_services_total": manual_services_total,
        "manual_parts_total": manual_parts_total,
        "manual_items_total": manual_items_total,
        "inventory_parts_total": inventory_parts_total,
        "labor_cost": labor_cost,
        "extra_parts_cost": extra_parts_cost,
        "parts_cost": extra_parts_cost,
        "gross_total": gross_total,
        "financial_subtotal": gross_total,
        "discount": discount,
        "net_total": net_total,
        "financial_total": net_total,
        "billable_inventory_parts_count": get_billable_inventory_parts(
            service_order
        ).count(),
        "generated_at": timezone.now(),
    }
