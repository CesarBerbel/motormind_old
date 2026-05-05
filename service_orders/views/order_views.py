from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.exceptions import DomainError, PermissionDeniedError
from core.permissions import (
    can_cancel_service_order,
    can_manage_service_orders,
    can_update_service_order_technical_data,
    can_view_service_orders,
    user_passes_permission,
)
from service_orders.ai_description import improve_problem_description
from service_orders.forms import (
    ServiceOrderApprovalForm,
    ServiceOrderCreateForm,
    ServiceOrderForm,
    ServiceOrderNoteForm,
    ServiceOrderTechnicalForm,
)
from service_orders.models import ServiceOrder
from service_orders.selectors import (
    filter_service_orders_by_search,
    get_all_inventory_parts_for_service_order,
    get_service_order_financial_summary,
    get_service_orders_for_list,
)
from service_orders.services import (
    approve_service_order_budget,
    change_service_order_status,
    create_service_order_from_form,
    update_service_order_from_form,
    update_service_order_technical_from_form,
)
from service_orders.services import cancel_service_order as cancel_service_order_service

from .common import redirect_if_canceled

try:
    from crm.selectors import get_service_order_crm_timeline
except ImportError:
    get_service_order_crm_timeline = None


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_list_view(request):
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
    if request.method == "POST":
        form = ServiceOrderCreateForm(request.POST)

        if form.is_valid():
            service_order = create_service_order_from_form(
                form=form,
                created_by=request.user,
            )

            messages.success(request, "Ordem de serviço criada com sucesso.")

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível criar a ordem de serviço. Verifique os dados informados.",
        )
    else:
        form = ServiceOrderCreateForm()

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Criar ordem de serviço",
            "button_text": "Salvar ordem de serviço",
            "show_problem_description_ai": True,
        },
    )


@login_required
@require_POST
@user_passes_permission(can_manage_service_orders)
def improve_problem_description_view(request):
    description = request.POST.get("description", "").strip()

    if not description:
        return JsonResponse(
            {"success": False, "error": "Informe a descrição do problema antes de usar a IA."},
            status=400,
        )

    if len(description) < 10:
        return JsonResponse(
            {"success": False, "error": "A descrição está muito curta para ser melhorada com segurança."},
            status=400,
        )

    try:
        improved_description = improve_problem_description(
            user=request.user,
            description=description,
        )
    except PermissionDeniedError as error:
        return JsonResponse(
            {"success": False, "error": str(error)},
            status=403,
        )
    except DomainError:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Não foi possível usar a IA agora. "
                    "Tente novamente em alguns instantes ou ajuste o texto manualmente."
                ),
            },
            status=503,
        )

    return JsonResponse(
        {
            "success": True,
            "description": improved_description,
        }
    )


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_detail_view(request, pk):
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
    financial_summary = get_service_order_financial_summary(service_order)
    crm_timeline = (
        get_service_order_crm_timeline(service_order)
        if get_service_order_crm_timeline
        else []
    )

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
            "inventory_parts_total": financial_summary["inventory_parts_total"],
            "manual_items_total": financial_summary["manual_items_total"],
            "financial_subtotal": financial_summary["gross_total"],
            "financial_total": financial_summary["net_total"],
            "financial_summary": financial_summary,
            "note_form": ServiceOrderNoteForm(),
            "approval_form": ServiceOrderApprovalForm(),
            "approval": getattr(service_order, "approval", None),
            "crm_timeline": crm_timeline,
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_update_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderForm(request.POST, instance=service_order)

        if form.is_valid():
            try:
                updated_service_order = update_service_order_from_form(
                    form=form,
                    changed_by=request.user,
                    old_instance=old_instance,
                )
            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, error.messages[0])
            else:

                messages.success(request, "Ordem de serviço atualizada com sucesso.")

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
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderTechnicalForm(request.POST, instance=service_order)

        if form.is_valid():
            try:
                updated_service_order = update_service_order_technical_from_form(
                    form=form,
                    changed_by=request.user,
                    old_instance=old_instance,
                )
            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, error.messages[0])
            else:

                messages.success(request, "Dados técnicos atualizados com sucesso.")

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
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    if request.method == "POST":
        try:
            canceled_service_order = cancel_service_order_service(
                service_order=service_order,
                changed_by=request.user,
            )
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect("service_orders:service_order_detail", pk=service_order.pk)

        messages.warning(request, "Ordem de serviço cancelada com sucesso.")

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


@login_required
@user_passes_permission(can_manage_service_orders)
@require_POST
def service_order_quick_status_update_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    new_status = request.POST.get("status")
    valid_statuses = dict(ServiceOrder._meta.get_field("status").choices)

    if new_status not in valid_statuses:
        return JsonResponse(
            {
                "ok": False,
                "error": "Status inválido.",
            },
            status=400,
        )

    if service_order.status == ServiceOrder.Status.CANCELED:
        return JsonResponse(
            {
                "ok": False,
                "error": "Ordens canceladas não podem ser alteradas.",
            },
            status=400,
        )

    try:
        service_order = change_service_order_status(
            service_order=service_order,
            new_status=new_status,
            changed_by=request.user,
        )
    except ValidationError as error:
        return JsonResponse(
            {
                "ok": False,
                "error": error.messages[0],
            },
            status=400,
        )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "status": service_order.status,
                "status_label": service_order.get_status_display(),
            }
        )

    messages.success(request, "Status da ordem atualizado com sucesso.")

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("service_orders:service_order_board")


@login_required
@user_passes_permission(can_manage_service_orders)
@require_POST
def service_order_approve_budget_view(request, pk):
    service_order = get_object_or_404(
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
        ),
        pk=pk,
    )

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    form = ServiceOrderApprovalForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Não foi possível aprovar o orçamento. Verifique o canal e as observações.",
        )
        return redirect("service_orders:service_order_detail", pk=service_order.pk)

    try:
        approve_service_order_budget(
            service_order=service_order,
            form=form,
            approved_by=request.user,
        )
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(
            request, "Orçamento aprovado e snapshot financeiro registrado."
        )

    return redirect("service_orders:service_order_detail", pk=service_order.pk)
