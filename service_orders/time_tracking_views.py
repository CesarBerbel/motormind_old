from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from accounts.permissions import groups_required

from .forms import ServiceOrderTimeEntryFinishForm
from .models import ServiceOrder, ServiceOrderTimeEntry


@login_required
@groups_required(["Administrador", "Mecânico"])
def service_order_time_start_view(request, pk):
    """
    Start a time entry for the current mechanic.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    if service_order.status == ServiceOrder.Status.CANCELED:
        messages.error(
            request,
            "Não é possível iniciar tempo em uma ordem cancelada.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    open_entry_exists = ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
        mechanic=request.user,
        ended_at__isnull=True,
    ).exists()

    if open_entry_exists:
        messages.warning(
            request,
            "Você já possui um apontamento de tempo em aberto para esta OS.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=request.user,
        started_at=timezone.now(),
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
@groups_required(["Administrador", "Mecânico"])
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

    if not request.user.groups.filter(name="Administrador").exists():
        if time_entry.mechanic != request.user:
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
            finished_entry = form.save(commit=False)
            finished_entry.ended_at = timezone.now()
            finished_entry.save()

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