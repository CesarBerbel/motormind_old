from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.permissions import can_access_productivity_report, user_passes_permission
from service_orders.models import ServiceOrderTimeEntry


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


def seconds_to_hours_minutes(total_seconds):
    """
    Convert seconds to a readable hours and minutes string.
    """
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return f"{hours}h {minutes}min"


@login_required
@user_passes_permission(can_access_productivity_report)
def mechanic_productivity_report_view(request):
    """
    Show mechanic productivity report based on closed time entries.
    """
    today = timezone.localdate()

    start_date_raw = request.GET.get("start_date", "")
    end_date_raw = request.GET.get("end_date", "")
    mechanic_id = request.GET.get("mechanic", "")

    start_date = parse_date(start_date_raw) if start_date_raw else today.replace(day=1)
    end_date = parse_date(end_date_raw) if end_date_raw else today

    if start_date is None:
        start_date = today.replace(day=1)

    if end_date is None:
        end_date = today

    start_datetime = timezone.make_aware(
        timezone.datetime.combine(
            start_date,
            timezone.datetime.min.time(),
        )
    )

    end_datetime = timezone.make_aware(
        timezone.datetime.combine(
            end_date,
            timezone.datetime.max.time(),
        )
    )

    time_entries = (
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

    if mechanic_id:
        time_entries = time_entries.filter(
            mechanic_id=mechanic_id,
        )

    mechanic_rows = {}
    total_seconds = 0

    for entry in time_entries:
        duration_seconds = entry.duration.total_seconds()
        total_seconds += duration_seconds

        mechanic_key = entry.mechanic_id

        if mechanic_key not in mechanic_rows:
            mechanic_rows[mechanic_key] = {
                "mechanic": entry.mechanic,
                "entries_count": 0,
                "total_seconds": 0,
                "orders": {},
            }

        mechanic_rows[mechanic_key]["entries_count"] += 1
        mechanic_rows[mechanic_key]["total_seconds"] += duration_seconds

        order_key = entry.service_order_id

        if order_key not in mechanic_rows[mechanic_key]["orders"]:
            mechanic_rows[mechanic_key]["orders"][order_key] = {
                "service_order": entry.service_order,
                "entries_count": 0,
                "total_seconds": 0,
            }

        mechanic_rows[mechanic_key]["orders"][order_key]["entries_count"] += 1
        mechanic_rows[mechanic_key]["orders"][order_key]["total_seconds"] += (
            duration_seconds
        )

    report_rows = []

    for row in mechanic_rows.values():
        orders = []

        for order in row["orders"].values():
            orders.append(
                {
                    "service_order": order["service_order"],
                    "entries_count": order["entries_count"],
                    "total_duration": seconds_to_hours_minutes(
                        order["total_seconds"],
                    ),
                }
            )

        report_rows.append(
            {
                "mechanic": row["mechanic"],
                "entries_count": row["entries_count"],
                "total_duration": seconds_to_hours_minutes(
                    row["total_seconds"],
                ),
                "orders": orders,
            }
        )

    return render(
        request,
        "service_orders/mechanic_productivity_report.html",
        {
            "report_rows": report_rows,
            "mechanics": get_mechanic_queryset(),
            "selected_mechanic": mechanic_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_duration": seconds_to_hours_minutes(total_seconds),
            "total_entries": time_entries.count(),
        },
    )
