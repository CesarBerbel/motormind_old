from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import can_manage_service_order_items, user_passes_permission
from service_orders.forms import ServiceOrderItemForm
from service_orders.models import ServiceOrder, ServiceOrderItem

from .common import redirect_if_canceled


@login_required
@user_passes_permission(can_manage_service_order_items)
def service_order_item_add_view(request, pk):
    """
    Add an item to a service order.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    if service_order.is_budget_approved:
        messages.error(
            request,
            "Orçamento aprovado não permite adicionar, editar ou excluir itens.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.service_order = service_order
            item.save()

            messages.success(
                request,
                "Item adicionado com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível adicionar o item. Verifique os dados informados.",
        )

    else:
        form = ServiceOrderItemForm()

    return render(
        request,
        "service_orders/service_order_item_form.html",
        {
            "form": form,
            "service_order": service_order,
            "page_title": "Adicionar item",
            "button_text": "Salvar item",
        },
    )


@login_required
@user_passes_permission(can_manage_service_order_items)
def service_order_item_update_view(request, pk, item_pk):
    """
    Update an item from a service order.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    if service_order.is_budget_approved:
        messages.error(
            request,
            "Orçamento aprovado não permite adicionar, editar ou excluir itens.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    item = get_object_or_404(
        ServiceOrderItem,
        pk=item_pk,
        service_order=service_order,
    )

    if request.method == "POST":
        form = ServiceOrderItemForm(
            request.POST,
            instance=item,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Item atualizado com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar o item. Verifique os dados informados.",
        )

    else:
        form = ServiceOrderItemForm(instance=item)

    return render(
        request,
        "service_orders/service_order_item_form.html",
        {
            "form": form,
            "service_order": service_order,
            "item": item,
            "page_title": "Editar item",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_manage_service_order_items)
def service_order_item_delete_view(request, pk, item_pk):
    """
    Delete an item from a service order.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    if service_order.is_budget_approved:
        messages.error(
            request,
            "Orçamento aprovado não permite adicionar, editar ou excluir itens.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    item = get_object_or_404(
        ServiceOrderItem,
        pk=item_pk,
        service_order=service_order,
    )

    if request.method == "POST":
        item.delete()

        messages.success(
            request,
            "Item excluído com sucesso.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    return render(
        request,
        "service_orders/service_order_item_confirm_delete.html",
        {
            "service_order": service_order,
            "item": item,
        },
    )
