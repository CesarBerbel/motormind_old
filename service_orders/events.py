"""
Domain events for the service orders bounded context.

This module keeps side effects out of service methods. The service layer emits
small immutable events and the handlers decide what must happen after the
transaction commits.
"""

from dataclasses import dataclass, field
from typing import Any

from django.db import transaction


@dataclass(frozen=True)
class ServiceOrderDomainEvent:
    """
    Base immutable event emitted by service order workflows.
    """

    service_order_id: int
    user_id: int | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceOrderOpened(ServiceOrderDomainEvent):
    """
    Emitted when a service order is created.
    """


@dataclass(frozen=True)
class ServiceOrderStatusChanged(ServiceOrderDomainEvent):
    """
    Emitted when a service order changes status.
    """

    old_status: str = ""
    new_status: str = ""


@dataclass(frozen=True)
class ServiceOrderBudgetApproved(ServiceOrderDomainEvent):
    """
    Emitted when a service order budget is formally approved.
    """

    approval_id: int | None = None


@dataclass(frozen=True)
class ServiceOrderCanceled(ServiceOrderDomainEvent):
    """
    Emitted when a service order is canceled.
    """


_EVENT_HANDLER_REGISTRY = {
    ServiceOrderOpened: [
        "service_orders.event_handlers.register_crm_service_order_opened",
        "service_orders.event_handlers.enqueue_service_order_opened_message",
    ],
    ServiceOrderStatusChanged: [
        "service_orders.event_handlers.register_crm_service_order_status_changed",
        "service_orders.event_handlers.create_receivable_when_service_order_is_finished",
        "service_orders.event_handlers.enqueue_vehicle_ready_message",
    ],
    ServiceOrderBudgetApproved: [
        "service_orders.event_handlers.register_crm_service_order_budget_approved",
    ],
    ServiceOrderCanceled: [
        "service_orders.event_handlers.register_crm_service_order_canceled",
    ],
}


def _import_string(dotted_path):
    """
    Import a callable from a dotted path without depending on django.utils internals.
    """
    module_path, function_name = dotted_path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[function_name])
    return getattr(module, function_name)


def dispatch_domain_event(event):
    """
    Dispatch a domain event synchronously to registered handlers.

    Handlers must be idempotent because they can be called after retries or by
    future management commands that replay events.
    """
    for dotted_path in _EVENT_HANDLER_REGISTRY.get(type(event), []):
        handler = _import_string(dotted_path)
        handler(event)


def dispatch_domain_event_on_commit(event):
    """
    Dispatch event only after the current database transaction commits.

    This prevents external side effects, CRM entries or financial records from
    being created for a service order change that was later rolled back.
    """
    transaction.on_commit(lambda: dispatch_domain_event(event))
