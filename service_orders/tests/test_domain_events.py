from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from financial.models import Receivable
from service_orders.event_handlers import (
    create_receivable_when_service_order_is_finished,
)
from service_orders.events import ServiceOrderStatusChanged
from service_orders.models import ServiceOrder


@pytest.fixture
def finished_order_data():
    User = get_user_model()
    user = User.objects.create_user(
        email="domain-events@example.com",
        password="StrongPassword123",
    )
    customer = Customer.objects.create(
        name="Cliente Eventos",
        phone="11999999999",
    )
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="EVT1234",
        brand="Honda",
        model="Civic",
    )
    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS com evento",
        description="Validar evento de domínio.",
        status=ServiceOrder.Status.FINISHED,
        labor_cost=Decimal("250.00"),
    )
    return {
        "user": user,
        "service_order": service_order,
    }


@pytest.mark.django_db
def test_finished_status_event_creates_receivable(finished_order_data):
    service_order = finished_order_data["service_order"]
    user = finished_order_data["user"]

    event = ServiceOrderStatusChanged(
        service_order_id=service_order.pk,
        user_id=user.pk,
        old_status=ServiceOrder.Status.IN_PROGRESS,
        new_status=ServiceOrder.Status.FINISHED,
    )

    create_receivable_when_service_order_is_finished(event)

    receivable = Receivable.objects.get(service_order=service_order)
    assert receivable.customer == service_order.customer
    assert receivable.created_by == user
    assert receivable.final_amount == service_order.total_amount


@pytest.mark.django_db
def test_finished_status_event_is_idempotent(finished_order_data):
    service_order = finished_order_data["service_order"]
    user = finished_order_data["user"]

    event = ServiceOrderStatusChanged(
        service_order_id=service_order.pk,
        user_id=user.pk,
        old_status=ServiceOrder.Status.IN_PROGRESS,
        new_status=ServiceOrder.Status.FINISHED,
    )

    create_receivable_when_service_order_is_finished(event)
    create_receivable_when_service_order_is_finished(event)

    assert Receivable.objects.filter(service_order=service_order).count() == 1


@pytest.mark.django_db
def test_non_finished_status_event_does_not_create_receivable(finished_order_data):
    service_order = finished_order_data["service_order"]
    user = finished_order_data["user"]

    event = ServiceOrderStatusChanged(
        service_order_id=service_order.pk,
        user_id=user.pk,
        old_status=ServiceOrder.Status.APPROVED,
        new_status=ServiceOrder.Status.IN_PROGRESS,
    )

    create_receivable_when_service_order_is_finished(event)

    assert not Receivable.objects.filter(service_order=service_order).exists()
