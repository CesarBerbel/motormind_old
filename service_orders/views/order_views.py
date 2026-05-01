from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import (
    can_cancel_service_order,
    can_manage_service_orders,
    can_update_service_order_technical_data,
    can_view_service_orders,
    user_passes_permission,
)
from service_orders.forms import (
    ServiceOrderForm,
    ServiceOrderNoteForm,
    ServiceOrderTechnicalForm,
)
from service_orders.models import ServiceOrder
from service_orders.selectors import (
    calculate_inventory_parts_total,
    filter_service_orders_by_search,
    get_all_inventory_parts_for_service_order,
    get_service_orders_for_list,
)
from service_orders.services import cancel_service_order as cancel_service_order_service
from service_orders.services import (
    create_service_order_from_form,
    update_service_order_from_form,
    update_service_order_technical_from_form,
)

from .common import redirect_if_canceled


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_list_view(request):
    """
    List service orders with filters.
    """
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")

    service_orders = get_service_orders_for_list()
    service_orders = filter_service_orders_by_search(service_orders, search)

    if status:
        service_orders = service_orders.filter(status=status)

    if priority:
        service_orders = service_orders.filter(priority=priority)

    return render(
        request,
        "service_orders/service_order_list.html",
        {
            "service_orders": service_orders,
            "search": search,
            "status": status,
            "priority": priority,
            "status_choices": ServiceOrder.Status.choices,
            "priority_choices": ServiceOrder.Priority.choices,
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_create_view(request):
    """
    Create a new service order.
    """
    if request.method == "POST":
        form = ServiceOrderForm(request.POST)

        if form.is_valid():
            service_order = create_service_order_from_form(
                form=form,
                created_by=request.user,
            )

            messages.success(
                request,
                "Ordem de serviço criada com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível criar a ordem de serviço. Verifique os dados informados.",
        )

    else:
        form = ServiceOrderForm()

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Criar ordem de serviço",
            "button_text": "Salvar ordem de serviço",
        },
    )


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_detail_view(request, pk):
    """
    Show service order details.
    """
    service_order = get_object_or_404(
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
            "created_by",
            "assigned_mechanic",
        ).prefetch_related(
            "items",
            "notes",
            "history",
            "time_entries",
            "inventory_parts",
        ),
        pk=pk,
    )

    items = service_order.items.all()
    notes = service_order.notes.select_related("created_by").all()
    histories = service_order.history.select_related("changed_by").all()
    time_entries = service_order.time_entries.select_related("mechanic").all()

    open_time_entry = time_entries.filter(
        mechanic=request.user,
        ended_at__isnull=True,
    ).first()

    inventory_parts = get_all_inventory_parts_for_service_order(service_order)
    inventory_parts_total = calculate_inventory_parts_total(service_order)

    manual_items_total = sum(item.total for item in items)

    financial_subtotal = (
        service_order.labor_cost
        + service_order.parts_cost
        + manual_items_total
        + inventory_parts_total
    )

    financial_total = financial_subtotal - service_order.discount

    if financial_total < 0:
        financial_total = 0

    return render(
        request,
        "service_orders/service_order_detail.html",
        {
            "service_order": service_order,
            "items": items,
            "notes": notes,
            "histories": histories,
            "time_entries": time_entries,
            "open_time_entry": open_time_entry,
            "inventory_parts": inventory_parts,
            "inventory_parts_total": inventory_parts_total,
            "manual_items_total": manual_items_total,
            "financial_subtotal": financial_subtotal,
            "financial_total": financial_total,
            "note_form": ServiceOrderNoteForm(),
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_update_view(request, pk):
    """
    Update administrative data.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderForm(
            request.POST,
            instance=service_order,
        )

        if form.is_valid():
            updated_service_order = update_service_order_from_form(
                form=form,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(
                request,
                "Ordem de serviço atualizada com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=updated_service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar a ordem de serviço. Verifique os dados informados.",
        )

    else:
        form = ServiceOrderForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Editar ordem de serviço",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_update_service_order_technical_data)
def service_order_technical_update_view(request, pk):
    """
    Update technical data.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderTechnicalForm(
            request.POST,
            instance=service_order,
        )

        if form.is_valid():
            updated_service_order = update_service_order_technical_from_form(
                form=form,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(
                request,
                "Dados técnicos atualizados com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=updated_service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar os dados técnicos. Verifique os dados informados.",
        )

    else:
        form = ServiceOrderTechnicalForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Atualizar dados técnicos",
            "button_text": "Salvar dados técnicos",
        },
    )


@login_required
@user_passes_permission(can_cancel_service_order)
def service_order_cancel_view(request, pk):
    """
    Cancel service order.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    if request.method == "POST":
        canceled_service_order = cancel_service_order_service(
            service_order=service_order,
            changed_by=request.user,
        )

        messages.warning(
            request,
            "Ordem de serviço cancelada com sucesso.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=canceled_service_order.pk,
        )

    return render(
        request,
        "service_orders/service_order_confirm_cancel.html",
        {
            "service_order": service_order,
        },
    )
