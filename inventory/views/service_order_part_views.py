from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import can_move_inventory_stock, user_passes_permission
from inventory.forms import ServiceOrderPartForm
from inventory.models import ServiceOrderPart
from inventory.services import (
    cancel_reserved_service_order_part,
    confirm_service_order_part_usage,
    reserve_part_for_service_order,
    return_used_service_order_part,
)
from service_orders.models import ServiceOrder


@login_required
@user_passes_permission(can_move_inventory_stock)
def service_order_part_add_view(request, service_order_pk):
    """
    Reserve an inventory part for a service order.
    """
    service_order = get_object_or_404(ServiceOrder, pk=service_order_pk)

    if service_order.status == ServiceOrder.Status.CANCELED:
        messages.error(request, "Não é possível adicionar peças em uma OS cancelada.")

        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderPartForm(request.POST)

        if form.is_valid():
            try:
                reserve_part_for_service_order(
                    service_order=service_order,
                    form=form,
                    created_by=request.user,
                )

                messages.success(request, "Peça reservada para a OS com sucesso.")

                return redirect(
                    "service_orders:service_order_detail", pk=service_order.pk
                )

            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, "Não foi possível reservar a peça.")

        else:
            messages.error(
                request, "Não foi possível reservar a peça. Verifique os dados."
            )

    else:
        form = ServiceOrderPartForm()

    return render(
        request,
        "inventory/service_order_part_form.html",
        {
            "form": form,
            "service_order": service_order,
        },
    )


@login_required
@user_passes_permission(can_move_inventory_stock)
def service_order_part_confirm_usage_view(request, service_order_pk, pk):
    """
    Confirm usage of a reserved service order part.
    """
    service_order_part = get_object_or_404(
        ServiceOrderPart,
        pk=pk,
        service_order_id=service_order_pk,
    )

    if request.method == "POST":
        try:
            confirm_service_order_part_usage(service_order_part=service_order_part)
            messages.success(request, "Uso da peça confirmado com sucesso.")
        except ValidationError as error:
            messages.error(request, error.message)

    return redirect("service_orders:service_order_detail", pk=service_order_pk)


@login_required
@user_passes_permission(can_move_inventory_stock)
def service_order_part_cancel_view(request, service_order_pk, pk):
    """
    Cancel a reserved service order part and release stock.
    """
    service_order_part = get_object_or_404(
        ServiceOrderPart,
        pk=pk,
        service_order_id=service_order_pk,
    )

    if request.method == "POST":
        try:
            cancel_reserved_service_order_part(
                service_order_part=service_order_part,
                changed_by=request.user,
            )

            messages.success(request, "Reserva da peça cancelada e estoque liberado.")

        except ValidationError as error:
            messages.error(request, error.message)

    return redirect("service_orders:service_order_detail", pk=service_order_pk)


@login_required
@user_passes_permission(can_move_inventory_stock)
def service_order_part_return_view(request, service_order_pk, pk):
    """
    Return a used service order part back to stock.
    """
    service_order_part = get_object_or_404(
        ServiceOrderPart,
        pk=pk,
        service_order_id=service_order_pk,
    )

    if request.method == "POST":
        try:
            return_used_service_order_part(
                service_order_part=service_order_part,
                changed_by=request.user,
            )

            messages.success(request, "Peça devolvida ao estoque com sucesso.")

        except ValidationError as error:
            messages.error(request, error.message)

    return redirect("service_orders:service_order_detail", pk=service_order_pk)
