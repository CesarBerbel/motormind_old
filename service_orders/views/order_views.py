from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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
    filter_service_orders_by_search,
    get_service_orders_for_list,
)
from service_orders.services import create_service_order_history

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
            service_order = form.save(commit=False)
            service_order.created_by = request.user
            service_order.save()

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
            "Erro ao criar ordem de serviço.",
        )

    else:
        form = ServiceOrderForm()

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Nova ordem de serviço",
            "button_text": "Salvar",
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
        ),
        pk=pk,
    )

    return render(
        request,
        "service_orders/service_order_detail.html",
        {
            "service_order": service_order,
            "note_form": ServiceOrderNoteForm(),
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_update_view(request, pk):
    """
    Update administrative data.
    """
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)
    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=pk)

    if request.method == "POST":
        form = ServiceOrderForm(request.POST, instance=service_order)

        if form.is_valid():
            updated = form.save(commit=False)

            if updated.status == ServiceOrder.Status.FINISHED:
                updated.finished_at = timezone.now()
            else:
                updated.finished_at = None

            updated.save()

            create_service_order_history(
                service_order=updated,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(request, "Ordem atualizada.")

            return redirect(
                "service_orders:service_order_detail",
                pk=pk,
            )

        messages.error(request, "Erro ao atualizar.")

    else:
        form = ServiceOrderForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Editar ordem",
            "button_text": "Salvar",
        },
    )


@login_required
@user_passes_permission(can_update_service_order_technical_data)
def service_order_technical_update_view(request, pk):
    """
    Update technical data (mechanic).
    """
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)
    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=pk)

    if request.method == "POST":
        form = ServiceOrderTechnicalForm(
            request.POST,
            instance=service_order,
        )

        if form.is_valid():
            updated = form.save(commit=False)

            if updated.status == ServiceOrder.Status.FINISHED:
                updated.finished_at = timezone.now()
            else:
                updated.finished_at = None

            updated.save()

            create_service_order_history(
                service_order=updated,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(request, "Dados técnicos atualizados.")

            return redirect(
                "service_orders:service_order_detail",
                pk=pk,
            )

        messages.error(request, "Erro ao atualizar dados técnicos.")

    else:
        form = ServiceOrderTechnicalForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Atualizar técnico",
            "button_text": "Salvar",
        },
    )


@login_required
@user_passes_permission(can_cancel_service_order)
def service_order_cancel_view(request, pk):
    """
    Cancel service order.
    """
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    if request.method == "POST":
        old_instance = ServiceOrder.objects.get(pk=pk)

        service_order.status = ServiceOrder.Status.CANCELED
        service_order.finished_at = None
        service_order.save()

        create_service_order_history(
            service_order=service_order,
            changed_by=request.user,
            old_instance=old_instance,
        )

        messages.warning(request, "Ordem cancelada.")

        return redirect(
            "service_orders:service_order_detail",
            pk=pk,
        )

    return render(
        request,
        "service_orders/service_order_confirm_cancel.html",
        {
            "service_order": service_order,
        },
    )
