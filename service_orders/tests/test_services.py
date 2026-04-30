from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderHistory
from service_orders.services import create_service_order_history


@pytest.fixture
def service_order_data():
    """
    Create default service order test data.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="audit@example.com",
        password="StrongPassword123",
    )

    customer = Customer.objects.create(
        name="Cliente Auditoria",
        phone="+351 910 000 000",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Título antigo",
        description="Descrição antiga",
        labor_cost=Decimal("10.00"),
        parts_cost=Decimal("20.00"),
        discount=Decimal("0.00"),
    )

    return {
        "user": user,
        "customer": customer,
        "vehicle": vehicle,
        "service_order": service_order,
    }


@pytest.mark.django_db
def test_create_service_order_history_records_changed_fields(service_order_data):
    """
    Test if history records are created for changed fields.
    """
    service_order = service_order_data["service_order"]
    user = service_order_data["user"]

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    service_order.title = "Título novo"
    service_order.labor_cost = Decimal("50.00")
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=user,
        old_instance=old_instance,
    )

    assert ServiceOrderHistory.objects.filter(
        service_order=service_order,
        field_name="title",
        old_value="Título antigo",
        new_value="Título novo",
    ).exists()

    assert ServiceOrderHistory.objects.filter(
        service_order=service_order,
        field_name="labor_cost",
        old_value="10.00",
        new_value="50.00",
    ).exists()


@pytest.mark.django_db
def test_create_service_order_history_ignores_unchanged_fields(service_order_data):
    """
    Test if no history is created when no audited field changed.
    """
    service_order = service_order_data["service_order"]
    user = service_order_data["user"]

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    create_service_order_history(
        service_order=service_order,
        changed_by=user,
        old_instance=old_instance,
    )

    assert ServiceOrderHistory.objects.count() == 0
