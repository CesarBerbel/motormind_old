from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone

from customers.models import Customer
from service_orders.models import ServiceOrder

from .models import Campaign, CustomerInteraction, CustomerOpportunity, CustomerReminder


def get_crm_dashboard_data():
    today = timezone.localdate()
    inactive_limit = today - timedelta(days=180)

    customers_with_last_order = Customer.objects.annotate(
        last_order_at=Max("service_orders__created_at"),
        open_opportunities_count=Count(
            "crm_opportunities",
            filter=Q(crm_opportunities__status=CustomerOpportunity.Status.OPEN),
        ),
    )

    inactive_customers = customers_with_last_order.filter(
        Q(last_order_at__date__lt=inactive_limit) | Q(last_order_at__isnull=True),
        is_active=True,
    )

    return {
        "total_customers": Customer.objects.filter(is_active=True).count(),
        "interactions_today": CustomerInteraction.objects.filter(
            interaction_date__date=today
        ).count(),
        "pending_reminders": CustomerReminder.objects.filter(
            status=CustomerReminder.Status.PENDING, due_date__lte=today
        ).count(),
        "open_opportunities": CustomerOpportunity.objects.filter(
            status=CustomerOpportunity.Status.OPEN
        ).count(),
        "active_campaigns": Campaign.objects.filter(
            status__in=[Campaign.Status.SCHEDULED, Campaign.Status.RUNNING]
        ).count(),
        "inactive_customers_count": inactive_customers.count(),
        "latest_interactions": CustomerInteraction.objects.select_related(
            "customer", "vehicle", "service_order", "responsible_user"
        )[:10],
        "due_reminders": CustomerReminder.objects.select_related(
            "customer", "vehicle", "service_order", "responsible_user"
        ).filter(status=CustomerReminder.Status.PENDING, due_date__lte=today)[:10],
        "inactive_customers": inactive_customers.order_by("last_order_at", "name")[:10],
    }


def get_customer_crm_summary(customer):
    return {
        "interactions": customer.crm_interactions.select_related(
            "vehicle", "service_order", "responsible_user"
        )[:10],
        "open_opportunities": customer.crm_opportunities.filter(
            status=CustomerOpportunity.Status.OPEN
        ).select_related("vehicle", "service_order", "responsible_user"),
        "pending_reminders": customer.crm_reminders.filter(
            status=CustomerReminder.Status.PENDING
        ).select_related("vehicle", "service_order", "responsible_user"),
    }


def get_service_order_crm_timeline(service_order):
    return service_order.crm_interactions.select_related(
        "customer", "vehicle", "responsible_user"
    ).all()


def get_inactive_customers(days=180):
    limit = timezone.localdate() - timedelta(days=days)
    return (
        Customer.objects.annotate(last_order_at=Max("service_orders__created_at"))
        .filter(
            Q(last_order_at__date__lt=limit) | Q(last_order_at__isnull=True),
            is_active=True,
        )
        .order_by("last_order_at", "name")
    )


def get_post_sale_candidates(days_after_finished=3):
    target_date = timezone.localdate() - timedelta(days=days_after_finished)
    return (
        ServiceOrder.objects.select_related("customer", "vehicle")
        .filter(
            status=ServiceOrder.Status.FINISHED,
            finished_at__date__lte=target_date,
        )
        .exclude(
            crm_interactions__interaction_type=CustomerInteraction.InteractionType.POST_SALE,
        )
    )
