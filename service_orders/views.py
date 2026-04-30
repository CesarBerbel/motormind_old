from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import groups_required
from customers.models import Vehicle

from .forms import ServiceOrderForm, ServiceOrderItemForm, ServiceOrderTechnicalForm
from .models import ServiceOrder
from .services import create_service_order_history


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def service_order_list_view(request):
    """
    List service orders with search and status filter.
    """
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")

    service_orders = ServiceOrder.objects.select_related(
        "customer",
        "vehicle",
        "created_by",
    )

    if search:
        service_orders = service_orders.filter(
            Q(customer__name__icontains=search)
            | Q(vehicle__plate__icontains=search)
            | Q(title__icontains=search)
            | Q(description__icontains=search)
        )

    if status:
        service_orders = service_orders.filter(status=status)

    return render(
        request,
        "service_orders/service_order_list.html",
        {
            "service_orders": service_orders,
            "search": search,
            "status": status,
            "status_choices": ServiceOrder.Status.choices,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
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
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def service_order_detail_view(request, pk):
    """
    Show service order details with audit history.
    """
    service_order = get_object_or_404(
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
            "created_by",
        ).prefetch_related("history"),
        pk=pk,
    )

    histories = service_order.history.select_related("changed_by").all()

    return render(
        request,
        "service_orders/service_order_detail.html",
        {
            "service_order": service_order,
            "histories": histories,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def service_order_update_view(request, pk):
    """
    Update a service order by administrator or attendant.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    if service_order.status == ServiceOrder.Status.CANCELED:
        messages.error(
            request,
            "Ordens de serviço canceladas não podem ser editadas.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderForm(
            request.POST,
            instance=service_order,
        )

        if form.is_valid():
            updated_order = form.save(commit=False)

            if (
                updated_order.status == ServiceOrder.Status.FINISHED
                and not updated_order.finished_at
            ):
                updated_order.finished_at = timezone.now()

            if updated_order.status != ServiceOrder.Status.FINISHED:
                updated_order.finished_at = None

            updated_order.save()

            create_service_order_history(
                service_order=updated_order,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(
                request,
                "Ordem de serviço atualizada com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
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
@groups_required(["Administrador", "Mecânico"])
def service_order_technical_update_view(request, pk):
    """
    Update technical fields by mechanic or administrator.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    if service_order.status == ServiceOrder.Status.CANCELED:
        messages.error(
            request,
            "Ordens de serviço canceladas não podem ser editadas.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderTechnicalForm(
            request.POST,
            instance=service_order,
        )

        if form.is_valid():
            updated_order = form.save(commit=False)

            if (
                updated_order.status == ServiceOrder.Status.FINISHED
                and not updated_order.finished_at
            ):
                updated_order.finished_at = timezone.now()

            if updated_order.status != ServiceOrder.Status.FINISHED:
                updated_order.finished_at = None

            updated_order.save()

            create_service_order_history(
                service_order=updated_order,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(
                request,
                "Dados técnicos atualizados com sucesso.",
            )

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
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
@groups_required(["Administrador"])
def service_order_cancel_view(request, pk):
    """
    Cancel a service order instead of deleting it.
    """
    service_order = get_object_or_404(
        ServiceOrder,
        pk=pk,
    )

    if request.method == "POST":
        old_instance = ServiceOrder.objects.get(pk=service_order.pk)

        service_order.status = ServiceOrder.Status.CANCELED
        service_order.finished_at = None
        service_order.save()

        create_service_order_history(
            service_order=service_order,
            changed_by=request.user,
            old_instance=old_instance,
        )

        messages.warning(
            request,
            "Ordem de serviço cancelada com sucesso.",
        )

        return redirect("service_orders:service_order_detail", pk=pk)

    return render(
        request,
        "service_orders/service_order_confirm_cancel.html",
        {
            "service_order": service_order,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicles_by_customer_view(request):
    """
    Return active vehicles from a selected customer as JSON.
    """
    customer_id = request.GET.get("customer_id")

    vehicles = Vehicle.objects.none()

    if customer_id:
        vehicles = Vehicle.objects.filter(
            customer_id=customer_id,
            is_active=True,
        ).order_by("plate")

    data = [
        {
            "id": vehicle.id,
            "text": f"{vehicle.plate} - {vehicle.brand} {vehicle.model}",
        }
        for vehicle in vehicles
    ]

    return JsonResponse(
        {
            "vehicles": data,
        }
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def service_order_item_add_view(request, pk):
    """
    Add item to service order.
    """
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    if request.method == "POST":
        form = ServiceOrderItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.service_order = service_order
            item.save()

            messages.success(request, "Item adicionado com sucesso.")

            return redirect("service_orders:service_order_detail", pk=pk)
    else:
        form = ServiceOrderItemForm()

    return render(
        request,
        "service_orders/service_order_item_form.html",
        {
            "form": form,
            "service_order": service_order,
        },
    )