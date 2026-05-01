from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.permissions import can_access_operational_board, user_passes_permission
from service_orders.models import ServiceOrder
from service_orders.services import create_service_order_history

from .common import redirect_if_canceled


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


def get_overdue_service_order_filter():
    """
    Return filter for overdue service orders.
    """
    today = timezone.localdate()

    return Q(expected_delivery_date__lt=today) & ~Q(
        status__in=[
            ServiceOrder.Status.FINISHED,
            ServiceOrder.Status.CANCELED,
        ]
    )


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
@user_passes_permission(can_access_operational_board)
def service_order_board_view(request):
    """
    Show an operational board grouped by service order status.
    """
    search = request.GET.get("search", "").strip()
    mechanic_id = request.GET.get("mechanic", "").strip()
    overdue = request.GET.get("overdue", "").strip()
    priority = request.GET.get("priority", "").strip()
    delivery_start = request.GET.get("delivery_start", "").strip()
    delivery_end = request.GET.get("delivery_end", "").strip()

    delivery_start_date = parse_date(delivery_start) if delivery_start else None
    delivery_end_date = parse_date(delivery_end) if delivery_end else None

    service_orders = (
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
            "created_by",
            "assigned_mechanic",
        )
        .annotate(
            priority_order=get_priority_ordering_annotation(),
        )
        .order_by(
            "priority_order",
            "expected_delivery_date",
            "created_at",
        )
    )

    if search:
        service_orders = service_orders.filter(
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

    if mechanic_id:
        service_orders = service_orders.filter(
            assigned_mechanic_id=mechanic_id,
        )

    if overdue == "1":
        service_orders = service_orders.filter(
            get_overdue_service_order_filter(),
        )

    if priority:
        service_orders = service_orders.filter(
            priority=priority,
        )

    if delivery_start and not delivery_start_date:
        messages.error(
            request,
            "Data inicial inválida. Use uma data válida no formato do campo.",
        )

    if delivery_end and not delivery_end_date:
        messages.error(
            request,
            "Data final inválida. Use uma data válida no formato do campo.",
        )

    if delivery_start_date:
        service_orders = service_orders.filter(
            expected_delivery_date__gte=delivery_start_date,
        )

    if delivery_end_date:
        service_orders = service_orders.filter(
            expected_delivery_date__lte=delivery_end_date,
        )

    status_columns = []

    for status_value, status_label in ServiceOrder.Status.choices:
        status_columns.append(
            {
                "value": status_value,
                "label": status_label,
                "orders": service_orders.filter(status=status_value),
            }
        )

    return render(
        request,
        "service_orders/service_order_board.html",
        {
            "status_columns": status_columns,
            "search": search,
            "mechanic_id": mechanic_id,
            "mechanics": get_mechanic_queryset(),
            "overdue": overdue,
            "priority": priority,
            "delivery_start": delivery_start,
            "delivery_end": delivery_end,
            "today": timezone.localdate(),
            "status_choices": ServiceOrder.Status.choices,
            "priority_choices": ServiceOrder.Priority.choices,
        },
    )


@login_required
@user_passes_permission(can_access_operational_board)
def service_order_quick_status_update_view(request, pk):
    """
    Quickly update service order status from operational board.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    if request.method != "POST":
        messages.error(
            request,
            "Método inválido para alterar status.",
        )

        return redirect("service_orders:service_order_board")

    new_status = request.POST.get("status")
    valid_statuses = [
        status_value for status_value, _label in ServiceOrder.Status.choices
    ]

    if new_status not in valid_statuses:
        messages.error(
            request,
            "Status informado é inválido.",
        )

        return redirect("service_orders:service_order_board")

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    service_order.status = new_status

    if service_order.status == ServiceOrder.Status.FINISHED:
        service_order.finished_at = timezone.now()
    else:
        service_order.finished_at = None

    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=request.user,
        old_instance=old_instance,
    )

    messages.success(
        request,
        "Status da ordem de serviço atualizado com sucesso.",
    )

    next_url = request.POST.get("next") or "service_orders:service_order_board"

    if next_url == "service_orders:service_order_board":
        return redirect("service_orders:service_order_board")

    return redirect(next_url)
