from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.permissions import groups_required
from service_orders.models import ServiceOrder


def get_priority_ordering_annotation():
    """
    Return priority ordering annotation.
    """
    return Case(
        When(priority=ServiceOrder.Priority.HIGH, then=Value(1)),
        When(priority=ServiceOrder.Priority.MEDIUM, then=Value(2)),
        When(priority=ServiceOrder.Priority.LOW, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico"])
def workshop_agenda_view(request):
    """
    Show workshop agenda using expected delivery dates.
    """
    selected_date_raw = request.GET.get("date", "")
    view_mode = request.GET.get("view", "week")

    selected_date = (
        parse_date(selected_date_raw) if selected_date_raw else timezone.localdate()
    )

    if selected_date is None:
        selected_date = timezone.localdate()

    if view_mode not in ["day", "week"]:
        view_mode = "week"

    if view_mode == "day":
        start_date = selected_date
        end_date = selected_date
    else:
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)

    service_orders = (
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

    agenda_days = []

    current_date = start_date

    while current_date <= end_date:
        agenda_days.append(
            {
                "date": current_date,
                "orders": service_orders.filter(expected_delivery_date=current_date),
            }
        )

        current_date += timedelta(days=1)

    previous_date = start_date - timedelta(days=7 if view_mode == "week" else 1)
    next_date = start_date + timedelta(days=7 if view_mode == "week" else 1)

    return render(
        request,
        "service_orders/workshop_agenda.html",
        {
            "agenda_days": agenda_days,
            "selected_date": selected_date,
            "start_date": start_date,
            "end_date": end_date,
            "previous_date": previous_date,
            "next_date": next_date,
            "view_mode": view_mode,
        },
    )
