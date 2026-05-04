from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.models import ServiceOrder
from service_orders.services.history_service import create_service_order_history


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

    return service_order


def update_service_order_from_form(form, changed_by, old_instance):
    """
    Update a service order from a valid administrative form and create audit history.
    """
    service_order = form.save(commit=False)
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


def update_service_order_technical_from_form(form, changed_by, old_instance):
    """
    Update technical fields from a valid mechanic form and create audit history.
    """
    service_order = form.save(commit=False)
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


def cancel_service_order(service_order, changed_by):
    """
    Cancel a service order and create audit history.
    """
    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

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

    return service_order
