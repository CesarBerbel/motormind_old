from decimal import Decimal

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
