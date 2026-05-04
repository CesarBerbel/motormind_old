from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderItem


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
def test_service_order_string_representation(customer, vehicle, django_user_model):
    user = django_user_model.objects.create_user(
        email="usuario@test.com",
        password="senha-teste-123",
        first_name="Usuário",
        last_name="Teste",
    )

    order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Teste",
        description="Teste",
    )

    assert order.number is not None
    assert order.number.startswith("OS-")

    assert str(order).startswith(f"OS {order.number}")
    assert customer.name in str(order)


@pytest.mark.django_db
def test_service_order_total_amount(django_user_model):
    """
    Test service order total amount using service items and discount.
    """
    user = django_user_model.objects.create_user(
        email="admin@example.com",
        password="testpass123",
    )

    customer = Customer.objects.create(
        name="João Silva",
        phone="11999999999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="ABC1234",
        brand="Volkswagen",
        model="Gol",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Troca de óleo",
        description="Troca de óleo e revisão básica",
        discount=Decimal("20.00"),
    )

    ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description="Mão de obra",
        quantity=Decimal("1.00"),
        unit_price=Decimal("150.00"),
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
