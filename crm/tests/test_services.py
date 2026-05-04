from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from crm.models import CustomerInteraction, CustomerReminder
from crm.services import (
    register_service_order_opened,
    register_service_order_status_change,
)
from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(email="admin@example.com", password="test123456")


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Cliente CRM", phone="11999999999", email="cliente@example.com"
    )


@pytest.fixture
def vehicle(customer):
    return Vehicle.objects.create(
        customer=customer, plate="CRM1234", brand="Fiat", model="Uno"
    )


@pytest.fixture
def service_order(customer, vehicle, user):
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Revisão",
        description="Revisão preventiva",
    )


@pytest.mark.django_db
def test_register_service_order_opened_creates_crm_interaction(service_order, user):
    interaction = register_service_order_opened(service_order, user)

    assert interaction.customer == service_order.customer
    assert interaction.service_order == service_order
    assert (
        interaction.interaction_type
        == CustomerInteraction.InteractionType.SERVICE_ORDER
    )


@pytest.mark.django_db
def test_finished_status_creates_post_sale_reminder(service_order, user):
    register_service_order_status_change(
        service_order,
        user,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.FINISHED,
    )

    reminder = CustomerReminder.objects.get(service_order=service_order)
    assert reminder.status == CustomerReminder.Status.PENDING
    assert reminder.due_date == timezone.localdate() + timedelta(days=3)
