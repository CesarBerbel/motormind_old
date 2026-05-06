from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.events import (
    ServiceOrderBudgetApproved,
    ServiceOrderCanceled,
    ServiceOrderOpened,
    ServiceOrderStatusChanged,
    dispatch_domain_event_on_commit,
)
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
        ServiceOrder.Status.IN_DIAGNOSIS,
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.IN_DIAGNOSIS: {
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.WAITING_APPROVAL: {
        ServiceOrder.Status.APPROVED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.APPROVED: {
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.IN_PROGRESS: {
        ServiceOrder.Status.WAITING_PARTS,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.WAITING_PARTS: {
        ServiceOrder.Status.IN_DIAGNOSIS,
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.FINISHED: {
        ServiceOrder.Status.BILLED,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.BILLED: {
        ServiceOrder.Status.PAID,
        ServiceOrder.Status.CANCELED,
    },
    ServiceOrder.Status.PAID: set(),
    ServiceOrder.Status.CANCELED: set(),
}

FINAL_FINISHED_AT_STATUSES = {
    ServiceOrder.Status.FINISHED,
    ServiceOrder.Status.BILLED,
    ServiceOrder.Status.PAID,
}

LOCKED_STATUSES = {
    ServiceOrder.Status.BILLED,
    ServiceOrder.Status.PAID,
    ServiceOrder.Status.CANCELED,
}


def apply_finished_at_by_status(service_order):
    """
    Apply finished_at according to final operational statuses.

    Finished, billed and paid orders keep the same finished_at timestamp.
    Reopening the order to a non-final operational status clears finished_at.
    """
    if service_order.status in FINAL_FINISHED_AT_STATUSES:
        if not service_order.finished_at:
            service_order.finished_at = timezone.now()
    else:
        service_order.finished_at = None

    return service_order


def get_allowed_next_statuses(current_status):
    """
    Return the valid next statuses for the current service order status.
    """
    return ALLOWED_STATUS_TRANSITIONS.get(current_status, set())


def get_allowed_next_status_choices(service_order):
    """
    Return choices for UI controls, keeping the current status as the first option.
    """
    allowed_statuses = get_allowed_next_statuses(service_order.status)
    choices = [(service_order.status, service_order.get_status_display())]

    for status_value, status_label in ServiceOrder.Status.choices:
        if status_value in allowed_statuses:
            choices.append((status_value, status_label))

    return choices


def ensure_service_order_is_not_locked(service_order):
    """
    Block operational edits on statuses that represent closed accounting states.
    """
    if service_order.status in LOCKED_STATUSES:
        raise ValidationError(
            f"Ordem com status {service_order.get_status_display()} não permite alterações operacionais."
        )


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


@transaction.atomic
def create_service_order_from_form(form, created_by):
    """
    Create a service order from a valid form and attach optional catalog items.
    """
    from workshop_services.services import (
        add_catalog_service_to_order,
        add_combo_to_order,
    )

    service_order = form.save(commit=False)
    service_order.created_by = created_by

    if service_order.order_type in [
        ServiceOrder.OrderType.WARRANTY,
        ServiceOrder.OrderType.RETURN,
    ]:
        service_order.warranty_approved_by = created_by
        service_order.warranty_approved_at = timezone.now()

    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    for catalog_service in form.cleaned_data.get("catalog_services", []):
        add_catalog_service_to_order(
            service_order=service_order,
            service=catalog_service,
            quantity=Decimal("1.00"),
            unit_price=None,
            created_by=created_by,
        )

    for combo in form.cleaned_data.get("service_combos", []):
        add_combo_to_order(
            service_order=service_order,
            combo=combo,
            created_by=created_by,
        )

    log_event(
        action=AuditLog.Action.SERVICE_ORDER_OPENED,
        user=created_by,
        obj=service_order,
        new_data=serialize_instance(service_order),
    )
    dispatch_domain_event_on_commit(
        ServiceOrderOpened(
            service_order_id=service_order.pk,
            user_id=getattr(created_by, "pk", None),
        )
    )

    return service_order


def update_service_order_from_form(form, changed_by, old_instance):
    """
    Update a service order from a valid administrative form and create audit history.
    """
    service_order = form.save(commit=False)
    ensure_service_order_is_not_locked(old_instance)
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
        dispatch_domain_event_on_commit(
            ServiceOrderStatusChanged(
                service_order_id=service_order.pk,
                user_id=getattr(changed_by, "pk", None),
                old_status=old_status,
                new_status=service_order.status,
            )
        )

    return service_order


def update_service_order_technical_from_form(form, changed_by, old_instance):
    """
    Update technical fields from a valid mechanic form and create audit history.
    """
    service_order = form.save(commit=False)
    ensure_service_order_is_not_locked(old_instance)
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

    if old_instance.status != service_order.status:
        dispatch_domain_event_on_commit(
            ServiceOrderStatusChanged(
                service_order_id=service_order.pk,
                user_id=getattr(changed_by, "pk", None),
                old_status=old_instance.status,
                new_status=service_order.status,
            )
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

    if (
        locked_order.status == ServiceOrder.Status.WAITING_PARTS
        and new_status == ServiceOrder.Status.IN_PROGRESS
        and not locked_order.is_budget_approved
    ):
        raise ValidationError(
            "Ordem aguardando peças só pode voltar para execução depois da aprovação do orçamento."
        )

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

    dispatch_domain_event_on_commit(
        ServiceOrderStatusChanged(
            service_order_id=locked_order.pk,
            user_id=getattr(changed_by, "pk", None),
            old_status=old_instance.status,
            new_status=locked_order.status,
        )
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

    if locked_order.status != ServiceOrder.Status.WAITING_APPROVAL:
        raise ValidationError(
            "Apenas ordens com status Aguardando aprovação podem ter orçamento aprovado."
        )

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

    dispatch_domain_event_on_commit(
        ServiceOrderBudgetApproved(
            service_order_id=locked_order.pk,
            user_id=getattr(approved_by, "pk", None),
            approval_id=approval.pk,
            metadata={
                "old_status": old_instance.status,
                "new_status": locked_order.status,
                "approved_total": str(approval.net_total),
                "channel": approval.channel,
            },
        )
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
    dispatch_domain_event_on_commit(
        ServiceOrderCanceled(
            service_order_id=service_order.pk,
            user_id=getattr(changed_by, "pk", None),
            metadata={"old_status": old_instance.status},
        )
    )

    return service_order
