from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.permissions import (
    can_finish_time_entry,
    can_track_service_order_time,
    user_passes_permission,
)
from service_orders.forms import ServiceOrderTimeEntryFinishForm
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry
from service_orders.services import (
    can_start_time_entry,
    finish_time_entry_from_form,
    mechanic_has_open_time_entry,
    start_time_entry,
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

    if not can_start_time_entry(service_order):
        messages.error(
            request,
            "Não é possível iniciar tempo em uma ordem cancelada.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    if mechanic_has_open_time_entry(
        service_order=service_order,
        mechanic=request.user,
    ):
        messages.warning(
            request,
            "Você já possui um apontamento de tempo em aberto para esta OS.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    start_time_entry(
        service_order=service_order,
        mechanic=request.user,
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

    if not can_finish_time_entry(request.user, time_entry):
        messages.error(
            request,
            "Você não pode encerrar apontamentos de outro mecânico.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    if request.method == "POST":
        form = ServiceOrderTimeEntryFinishForm(
            request.POST,
            instance=time_entry,
        )

        if form.is_valid():
            finish_time_entry_from_form(form)

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
