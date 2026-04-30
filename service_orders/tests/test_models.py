from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def service_order_data():
    """
    Create required data for service order tests.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="attendant@example.com",
        password="StrongPassword123",
    )

    customer = Customer.objects.create(
        name="Cliente Teste",
        phone="+351 910 000 000",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )

    return {
        "user": user,
        "customer": customer,
        "vehicle": vehicle,
    }


@pytest.mark.django_db
def test_service_order_string_representation(service_order_data):
    """
    Test service order string representation.
    """
    service_order = ServiceOrder.objects.create(
        customer=service_order_data["customer"],
        vehicle=service_order_data["vehicle"],
        created_by=service_order_data["user"],
        title="Troca de óleo",
        description="Cliente solicitou troca de óleo.",
    )

    assert str(service_order) == f"OS #{service_order.pk} - Cliente Teste"


@pytest.mark.django_db
def test_service_order_total_amount(service_order_data):
    """
    Test service order total amount calculation.
    """
    service_order = ServiceOrder.objects.create(
        customer=service_order_data["customer"],
        vehicle=service_order_data["vehicle"],
        created_by=service_order_data["user"],
        title="Revisão",
        description="Revisão geral.",
        labor_cost=Decimal("100.00"),
        parts_cost=Decimal("50.00"),
        discount=Decimal("20.00"),
    )

    assert service_order.total_amount == Decimal("130.00")


@pytest.mark.django_db
def test_service_order_total_amount_never_negative(service_order_data):
    """
    Test if service order total amount never returns negative value.
    """
    service_order = ServiceOrder.objects.create(
        customer=service_order_data["customer"],
        vehicle=service_order_data["vehicle"],
        created_by=service_order_data["user"],
        title="Desconto",
        description="Teste de desconto.",
        labor_cost=Decimal("10.00"),
        parts_cost=Decimal("10.00"),
        discount=Decimal("100.00"),
    )

    assert service_order.total_amount == Decimal("0.00")
