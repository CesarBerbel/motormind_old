"""
Side-effect handlers for service order domain events.

The handlers intentionally import other apps lazily. This keeps service_orders
as the workflow owner while avoiding hard failures when optional modules such as
CRM are unavailable or still being developed.
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from core.exceptions import ObjectAlreadyExistsError
from service_orders.models import ServiceOrder


def _get_service_order(event):
    return ServiceOrder.objects.select_related("customer", "vehicle").get(
        pk=event.service_order_id
    )


def _get_user(event):
    if not event.user_id:
        return None

    User = get_user_model()
    try:
        return User.objects.get(pk=event.user_id)
    except User.DoesNotExist:
        return None


def _try_get_crm_services():
    try:
        from crm import services as crm_services
    except ImportError:
        return None

    return crm_services


def register_crm_service_order_opened(event):
    """
    Register the OS opening in CRM when the CRM module is available.
    """
    crm_services = _try_get_crm_services()
    if not crm_services or not hasattr(crm_services, "register_service_order_opened"):
        return None

    return crm_services.register_service_order_opened(
        _get_service_order(event),
        _get_user(event),
    )


def register_crm_service_order_status_changed(event):
    """
    Register status changes in CRM when the CRM module is available.
    """
    crm_services = _try_get_crm_services()
    if not crm_services or not hasattr(
        crm_services, "register_service_order_status_change"
    ):
        return None

    return crm_services.register_service_order_status_change(
        _get_service_order(event),
        _get_user(event),
        event.old_status,
        event.new_status,
    )


def register_crm_service_order_budget_approved(event):
    """
    Register budget approval in CRM as a status transition event.
    """
    crm_services = _try_get_crm_services()
    if not crm_services or not hasattr(
        crm_services, "register_service_order_status_change"
    ):
        return None

    return crm_services.register_service_order_status_change(
        _get_service_order(event),
        _get_user(event),
        ServiceOrder.Status.WAITING_APPROVAL,
        ServiceOrder.Status.APPROVED,
    )


def register_crm_service_order_canceled(event):
    """
    Register cancellation in CRM when the CRM module is available.
    """
    crm_services = _try_get_crm_services()
    if not crm_services or not hasattr(crm_services, "register_service_order_canceled"):
        return None

    return crm_services.register_service_order_canceled(
        _get_service_order(event),
        _get_user(event),
    )


@transaction.atomic
def create_receivable_when_service_order_is_finished(event):
    """
    Automatically create a receivable when an OS becomes finished.

    This handler is idempotent: if the receivable already exists, nothing is
    duplicated. The service order remains in FINISHED; the transition to BILLED
    can still be explicit after financial review.
    """
    if event.new_status != ServiceOrder.Status.FINISHED:
        return None

    try:
        from financial.services import create_receivable_from_service_order
    except ImportError:
        return None

    service_order = ServiceOrder.objects.select_for_update().get(
        pk=event.service_order_id
    )

    if hasattr(service_order, "receivable"):
        return service_order.receivable

    try:
        return create_receivable_from_service_order(
            service_order=service_order,
            created_by=_get_user(event) or service_order.created_by,
        )
    except ObjectAlreadyExistsError:
        service_order.refresh_from_db()
        return getattr(service_order, "receivable", None)
