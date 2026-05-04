from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from core.exceptions import DomainError, PermissionDeniedError
from core.permissions import (
    can_track_service_order_time,
    user_passes_permission,
)
from service_orders.forms import ServiceOrderTimeEntryFinishForm
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry
from service_orders.services import (
    finish_time_entry,
    start_time_entry_for_service_order,
)


@login_required
@user_passes_permission(can_track_service_order_time)
def service_order_time_start_view(request, pk):
    """
    Start a time entry for the current mechanic.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    try:
        start_time_entry_for_service_order(
            service_order=service_order,
            mechanic=request.user,
        )
    except DomainError as exc:
        messages.error(
            request,
            exc.message,
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    messages.success(
        request,
        "Apontamento de tempo iniciado com sucesso.",
    )

    return redirect(
        "service_orders:service_order_detail",
        pk=service_order.pk,
    )


@login_required
@user_passes_permission(can_track_service_order_time)
def service_order_time_finish_view(request, pk, entry_pk):
    """
    Finish a time entry for the current mechanic.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    time_entry = get_object_or_404(
        ServiceOrderTimeEntry,
        pk=entry_pk,
        service_order=service_order,
        ended_at__isnull=True,
    )

    if request.method == "POST":
        form = ServiceOrderTimeEntryFinishForm(
            request.POST,
            instance=time_entry,
        )

        if form.is_valid():
            try:
                finish_time_entry(
                    time_entry=time_entry,
                    finished_by=request.user,
                    note=form.cleaned_data.get("note"),
                )
            except PermissionDeniedError as exc:
                messages.error(
                    request,
                    exc.message,
                )

                return redirect(
                    "service_orders:service_order_detail",
                    pk=service_order.pk,
                )
            except DomainError as exc:
                messages.error(
                    request,
                    exc.message,
                )

                return redirect(
                    "service_orders:service_order_detail",
                    pk=service_order.pk,
                )

            messages.success(
                request,
                "Apontamento de tempo encerrado com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível encerrar o apontamento.",
        )

    return redirect(
        "service_orders:service_order_detail",
        pk=service_order.pk,
    )
