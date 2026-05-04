"""
Read-only selectors for account dashboards and profile landing areas.

The atendimento area is a profile-specific operational dashboard. It must read
from customers, vehicles and service_orders without changing data in those apps.
"""

from django.db.models import Count, Q
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


def get_attendant_quick_search_results(query, limit=5):
    """
    Return quick search results for the attendant dashboard.

    The search is intentionally read-only and focused on the reception workflow:
    finding an existing customer or vehicle before opening a new service order.
    """
    cleaned_query = (query or "").strip()

    empty_result = {
        "query": cleaned_query,
        "customers": Customer.objects.none(),
        "vehicles": Vehicle.objects.none(),
        "has_query": bool(cleaned_query),
    }

    if not cleaned_query:
        return empty_result

    customers = (
        Customer.objects.filter(
            is_active=True,
        )
        .filter(
            Q(name__icontains=cleaned_query)
            | Q(phone__icontains=cleaned_query)
            | Q(email__icontains=cleaned_query)
            | Q(document__icontains=cleaned_query)
        )
        .order_by(
            "name",
        )[:limit]
    )

    vehicles = (
        Vehicle.objects.select_related(
            "customer",
        )
        .filter(
            is_active=True,
            customer__is_active=True,
        )
        .filter(
            Q(plate__icontains=cleaned_query)
            | Q(brand__icontains=cleaned_query)
            | Q(model__icontains=cleaned_query)
            | Q(customer__name__icontains=cleaned_query)
            | Q(customer__phone__icontains=cleaned_query)
            | Q(customer__document__icontains=cleaned_query)
        )
        .order_by(
            "plate",
        )[:limit]
    )

    return {
        "query": cleaned_query,
        "customers": customers,
        "vehicles": vehicles,
        "has_query": True,
    }


def get_attendant_dashboard_data(limit=8, search_query=""):
    """
    Return the operational data required by the attendant area.

    The attendant is responsible for customer reception, customer/vehicle
    registration, service order opening and operational follow-up. This selector
    keeps those reads centralized and avoids business logic inside the template.
    """
    today = timezone.localdate()

    active_statuses = [
        ServiceOrder.Status.OPEN,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.WAITING_APPROVAL,
    ]

    service_orders = ServiceOrder.objects.select_related(
        "customer",
        "vehicle",
        "assigned_mechanic",
    )

    open_orders = service_orders.filter(status=ServiceOrder.Status.OPEN)
    waiting_approval_orders = service_orders.filter(
        status=ServiceOrder.Status.WAITING_APPROVAL,
    )
    waiting_parts_orders = service_orders.filter(
        status=ServiceOrder.Status.WAITING_PARTS,
    )
    overdue_orders = service_orders.filter(
        expected_delivery_date__lt=today,
    ).exclude(
        status__in=[
            ServiceOrder.Status.FINISHED,
            ServiceOrder.Status.CANCELED,
        ],
    )

    recent_orders = service_orders.exclude(
        status=ServiceOrder.Status.CANCELED,
    ).order_by("expected_delivery_date", "-created_at",)[:limit]

    recent_customers = (
        Customer.objects.filter(
            is_active=True,
        )
        .annotate(
            active_orders_count=Count(
                "service_orders",
                filter=Q(service_orders__status__in=active_statuses),
            )
        )
        .order_by(
            "-created_at",
        )[:limit]
    )

    quick_search = get_attendant_quick_search_results(
        query=search_query,
        limit=limit,
    )

    return {
        "customers_count": Customer.objects.filter(is_active=True).count(),
        "vehicles_count": Vehicle.objects.filter(is_active=True).count(),
        "open_orders_count": open_orders.count(),
        "waiting_approval_orders_count": waiting_approval_orders.count(),
        "waiting_parts_orders_count": waiting_parts_orders.count(),
        "overdue_orders_count": overdue_orders.count(),
        "recent_orders": recent_orders,
        "recent_customers": recent_customers,
        "quick_search": quick_search,
    }


def get_main_dashboard_data(user):
    """
    Return shared counters for the main authenticated dashboard.
    """
    today = timezone.localdate()

    overdue_service_orders_count = (
        ServiceOrder.objects.filter(
            expected_delivery_date__lt=today,
        )
        .exclude(
            status__in=[
                ServiceOrder.Status.FINISHED,
                ServiceOrder.Status.CANCELED,
            ]
        )
        .count()
    )

    open_service_orders_count = ServiceOrder.objects.exclude(
        status__in=[
            ServiceOrder.Status.FINISHED,
            ServiceOrder.Status.CANCELED,
        ]
    ).count()

    assigned_to_me_count = (
        ServiceOrder.objects.filter(
            assigned_mechanic=user,
        )
        .exclude(
            status__in=[
                ServiceOrder.Status.FINISHED,
                ServiceOrder.Status.CANCELED,
            ]
        )
        .count()
    )

    return {
        "overdue_service_orders_count": overdue_service_orders_count,
        "open_service_orders_count": open_service_orders_count,
        "assigned_to_me_count": assigned_to_me_count,
    }
