from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.permissions import can_manage_service_order_notes, user_passes_permission
from service_orders.forms import ServiceOrderNoteForm
from service_orders.models import ServiceOrder

from .common import redirect_if_canceled


@login_required
@user_passes_permission(can_manage_service_order_notes)
def service_order_note_create_view(request, pk):
    """
    Create an internal note for a service order.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    if request.method == "POST":
        form = ServiceOrderNoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.service_order = service_order
            note.created_by = request.user
            note.save()

            messages.success(
                request,
                "Observação adicionada com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível adicionar a observação. Verifique os dados informados.",
        )

    return redirect(
        "service_orders:service_order_detail",
        pk=service_order.pk,
    )
