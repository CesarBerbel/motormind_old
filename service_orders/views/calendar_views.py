from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from core.permissions import can_access_workshop_agenda, user_passes_permission
from service_orders.selectors import get_agenda_service_orders


@login_required
@user_passes_permission(can_access_workshop_agenda)
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

    service_orders = get_agenda_service_orders(
        start_date=start_date,
        end_date=end_date,
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
