from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.models import ServiceOrder
from service_orders.selectors import get_service_order_financial_summary
from service_orders.services.history_service import create_service_order_history

FINANCIAL_FIELDS = {
    "labor_cost",
    "parts_cost",
    "discount",
}

ALLOWED_STATUS_TRANSITIONS = {
    ServiceOrder.Status.OPEN: {
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.IN_PROGRESS: {
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.WAITING_PARTS: {
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.WAITING_APPROVAL: {
        ServiceOrder.Status.APPROVED,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.APPROVED: {
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.FINISHED: {
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.CANCELED: set(),
}


def _safe_register_crm_event(function_name, *args, **kwargs):
    """Register CRM side effects without making OS workflow depend on CRM availability."""
    try:
        from crm import services as crm_services
    except ImportError:
        return None

    crm_function = getattr(crm_services, function_name, None)
    if not crm_function:
        return None

    return crm_function(*args, **kwargs)


def apply_finished_at_by_status(service_order):
    """
    Apply finished_at according to service order status.
    """
    if service_order.status == ServiceOrder.Status.FINISHED:
        if not service_order.finished_at:
            service_order.finished_at = timezone.now()
    else:
        service_order.finished_at = None

    return service_order


def validate_service_order_status_transition(old_status, new_status):
    """
    Validate a controlled service order status transition.
    """
    if old_status == new_status:
        return

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())

    if new_status not in allowed_statuses:
        old_label = ServiceOrder.Status(old_status).label
        new_label = ServiceOrder.Status(new_status).label
        raise ValidationError(
            f"Transição de status inválida: {old_label} -> {new_label}."
        )


def ensure_service_order_can_change_financial_data(service_order, old_instance):
    """
    Prevent financial changes after formal budget approval.
    """
    if not getattr(old_instance, "is_budget_approved", False):
        return

    for field_name in FINANCIAL_FIELDS:
        if getattr(service_order, field_name) != getattr(old_instance, field_name):
            raise ValidationError(
                "Orçamento aprovado não permite alteração de valores. "
                "Crie um fluxo de revisão de orçamento ou solicite ação administrativa."
            )


def create_service_order_from_form(form, created_by):
    """
    Create a service order from a valid form.
    """
    service_order = form.save(commit=False)
    service_order.created_by = created_by
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    log_event(
        action=AuditLog.Action.SERVICE_ORDER_OPENED,
        user=created_by,
        obj=service_order,
        new_data=serialize_instance(service_order),
    )
    _safe_register_crm_event("register_service_order_opened", service_order, created_by)

    return service_order


def update_service_order_from_form(form, changed_by, old_instance):
    """
    Update a service order from a valid administrative form and create audit history.
    """
    service_order = form.save(commit=False)
    validate_service_order_status_transition(old_instance.status, service_order.status)
    ensure_service_order_can_change_financial_data(service_order, old_instance)

    old_status = old_instance.status
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )
    if old_status != service_order.status:
        _safe_register_crm_event(
            "register_service_order_status_change",
            service_order,
            changed_by,
            old_status,
            service_order.status,
        )

    return service_order


def update_service_order_technical_from_form(form, changed_by, old_instance):
    """
    Update technical fields from a valid mechanic form and create audit history.
    """
    service_order = form.save(commit=False)
    validate_service_order_status_transition(old_instance.status, service_order.status)
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )

    return service_order


@transaction.atomic
def change_service_order_status(service_order, new_status, changed_by):
    """
    Change service order status through the controlled workflow.
    """
    locked_order = ServiceOrder.objects.select_for_update().get(pk=service_order.pk)
    old_instance = ServiceOrder.objects.get(pk=locked_order.pk)

    validate_service_order_status_transition(locked_order.status, new_status)

    locked_order.status = new_status
    locked_order = apply_finished_at_by_status(locked_order)
    locked_order.save(update_fields=["status", "finished_at", "updated_at"])

    create_service_order_history(
        service_order=locked_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=changed_by,
        obj=locked_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(locked_order),
    )

    return locked_order


def _json_safe_financial_summary(financial_summary):
    """
    Convert financial summary values to JSON-safe strings for snapshots.
    """
    snapshot = {}

    for key, value in financial_summary.items():
        if isinstance(value, Decimal):
            snapshot[key] = str(value)
        elif hasattr(value, "isoformat"):
            snapshot[key] = value.isoformat()
        else:
            snapshot[key] = value

    return snapshot


@transaction.atomic
def approve_service_order_budget(service_order, form, approved_by):
    """
    Register formal budget approval and freeze the approved financial snapshot.
    """
    locked_order = ServiceOrder.objects.select_for_update().get(pk=service_order.pk)

    if locked_order.status == ServiceOrder.Status.CANCELED:
        raise ValidationError("Ordem cancelada não pode ter orçamento aprovado.")

    if hasattr(locked_order, "approval"):
        raise ValidationError("Esta ordem de serviço já possui orçamento aprovado.")

    financial_summary = get_service_order_financial_summary(locked_order)

    approval = form.save(commit=False)
    approval.service_order = locked_order
    approval.approved_by = approved_by
    approval.customer_name_snapshot = locked_order.customer.name
    approval.vehicle_snapshot = (
        f"{locked_order.vehicle.plate} - "
        f"{locked_order.vehicle.brand} {locked_order.vehicle.model}"
    )
    approval.gross_total = financial_summary["gross_total"]
    approval.discount = financial_summary["discount"]
    approval.net_total = financial_summary["net_total"]
    approval.financial_summary_snapshot = _json_safe_financial_summary(
        financial_summary
    )
    approval.save()

    old_instance = ServiceOrder.objects.get(pk=locked_order.pk)

    if locked_order.status == ServiceOrder.Status.WAITING_APPROVAL:
        locked_order.status = ServiceOrder.Status.APPROVED
        locked_order.save(update_fields=["status", "updated_at"])

        create_service_order_history(
            service_order=locked_order,
            changed_by=approved_by,
            old_instance=old_instance,
        )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=approved_by,
        obj=locked_order,
        old_data=serialize_instance(old_instance),
        new_data={
            "approval_id": approval.pk,
            "approved_total": str(approval.net_total),
            "channel": approval.channel,
        },
    )

    _safe_register_crm_event(
        "register_service_order_status_change",
        locked_order,
        approved_by,
        old_instance.status,
        locked_order.status,
    )

    return approval


def cancel_service_order(service_order, changed_by):
    """
    Cancel a service order and create audit history.
    """
    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    validate_service_order_status_transition(
        service_order.status, ServiceOrder.Status.CANCELED
    )

    service_order.status = ServiceOrder.Status.CANCELED
    service_order.finished_at = None
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.SERVICE_ORDER_CANCELED,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )
    _safe_register_crm_event(
        "register_service_order_canceled", service_order, changed_by
    )

    return service_order
