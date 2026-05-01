from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import groups_required
from customers.models import Vehicle

from .forms import (
    ServiceOrderForm,
    ServiceOrderItemForm,
    ServiceOrderNoteForm,
    ServiceOrderTechnicalForm,
)
from .models import ServiceOrder, ServiceOrderItem
from .services import create_service_order_history


def service_order_is_canceled(service_order):
    """
    Check if service order is canceled.
    """
    return service_order.status == ServiceOrder.Status.CANCELED


def redirect_if_canceled(request, service_order):
    """
    Redirect user when trying to change a canceled service order.
    """
    if service_order_is_canceled(service_order):
        messages.error(
            request,
            "Ordens de serviço canceladas não podem ser alteradas.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    return None


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

    High priority comes first, then medium, then low.
    """
    return Case(
        When(priority=ServiceOrder.Priority.HIGH, then=Value(1)),
        When(priority=ServiceOrder.Priority.MEDIUM, then=Value(2)),
        When(priority=ServiceOrder.Priority.LOW, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def service_order_list_view(request):
    """
    List service orders with search, status and priority filter.
    """
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")

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
            "-created_at",
        )
    )

    if search:
        service_orders = service_orders.filter(
            Q(customer__name__icontains=search)
            | Q(vehicle__plate__icontains=search)
            | Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(assigned_mechanic__email__icontains=search)
        )

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
@groups_required(["Administrador", "Atendente", "Mecânico"])
def service_order_board_view(request):
    """
    Show an operational board grouped by service order status.
    """
    search = request.GET.get("search", "")
    mechanic_id = request.GET.get("mechanic", "")
    overdue = request.GET.get("overdue", "")
    priority = request.GET.get("priority", "")

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
            "today": timezone.localdate(),
            "status_choices": ServiceOrder.Status.choices,
            "priority_choices": ServiceOrder.Priority.choices,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico"])
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
    Show service order details with items, notes, financial summary and history.
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
        ),
        pk=pk,
    )

    items = service_order.items.all()
    notes = service_order.notes.select_related("created_by").all()
    histories = service_order.history.select_related("changed_by").all()
    note_form = ServiceOrderNoteForm()
    time_entries = service_order.time_entries.select_related("mechanic").all()
    open_time_entry = time_entries.filter(
        mechanic=request.user,
        ended_at__isnull=True,
    ).first()

    return render(
        request,
        "service_orders/service_order_detail.html",
        {
            "service_order": service_order,
            "items": items,
            "notes": notes,
            "histories": histories,
            "note_form": note_form,
            "time_entries": time_entries,
            "open_time_entry": open_time_entry,
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

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    return render(
        request,
        "service_orders/service_order_confirm_cancel.html",
        {
            "service_order": service_order,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
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
@groups_required(["Administrador", "Atendente"])
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
@groups_required(["Administrador", "Atendente"])
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


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico"])
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
