from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle
from inventory.forms import ServiceOrderPartForm
from inventory.models import Part, ServiceOrderPart
from inventory.services import (
    cancel_reserved_service_order_part,
    confirm_service_order_part_usage,
    reserve_part_for_service_order,
    return_used_service_order_part,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def users():
    """
    Create users for financial summary tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="inventory_summary_attendant@example.com",
        password="StrongPassword123",
    )

    attendant_group, _created = Group.objects.get_or_create(name="Atendente")
    attendant.groups.add(attendant_group)

    return {
        "attendant": attendant,
    }


@pytest.fixture
def service_order(users):
    """
    Create service order for financial summary tests.
    """
    customer = Customer.objects.create(
        name="Cliente Resumo Estoque",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="SUM-1234",
        brand="Fiat",
        model="Mobi",
    )

    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        title="OS resumo financeiro estoque",
        description="Teste de resumo financeiro com peças.",
        status=ServiceOrder.Status.OPEN,
        priority=ServiceOrder.Priority.MEDIUM,
        labor_cost=Decimal("100.00"),
        parts_cost=Decimal("50.00"),
        discount=Decimal("10.00"),
    )


@pytest.fixture
def part():
    """
    Create part for financial summary tests.
    """
    return Part.objects.create(
        name="Filtro de combustível",
        internal_code="FUEL-SUM-001",
        brand="Mann",
        category="Motor",
        unit="un",
        cost_price=Decimal("20.00"),
        sale_price=Decimal("80.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("2.00"),
    )


def reserve_part(service_order, part, user, quantity="2.00", unit_price="80.00"):
    """
    Helper to reserve part for service order.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    return reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=user,
    )


@pytest.mark.django_db
def test_service_order_detail_includes_reserved_inventory_parts_in_total(
    client,
    users,
    service_order,
    part,
):
    """
    Test if reserved inventory parts are included in service order financial summary.
    """
    reserve_part(
        service_order=service_order,
        part=part,
        user=users["attendant"],
        quantity="2.00",
        unit_price="80.00",
    )

    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse(
            "service_orders:service_order_detail",
            args=[service_order.pk],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "Peças do estoque" in content
    assert "R$ 160,00" in content
    assert "R$ 300,00" in content


@pytest.mark.django_db
def test_service_order_detail_includes_used_inventory_parts_in_total(
    client,
    users,
    service_order,
    part,
):
    """
    Test if used inventory parts are included in service order financial summary.
    """
    service_order_part = reserve_part(
        service_order=service_order,
        part=part,
        user=users["attendant"],
        quantity="2.00",
        unit_price="80.00",
    )

    confirm_service_order_part_usage(
        service_order_part=service_order_part,
    )

    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse(
            "service_orders:service_order_detail",
            args=[service_order.pk],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "R$ 160,00" in content
    assert "R$ 300,00" in content


@pytest.mark.django_db
def test_service_order_detail_excludes_canceled_inventory_parts_from_total(
    client,
    users,
    service_order,
    part,
):
    """
    Test if canceled inventory parts are not included in service order financial summary.
    """
    service_order_part = reserve_part(
        service_order=service_order,
        part=part,
        user=users["attendant"],
        quantity="2.00",
        unit_price="80.00",
    )

    cancel_reserved_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse(
            "service_orders:service_order_detail",
            args=[service_order.pk],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "Peças do estoque" in content
    assert "R$ 0,00" in content
    assert "R$ 140,00" in content


@pytest.mark.django_db
def test_service_order_detail_excludes_returned_inventory_parts_from_total(
    client,
    users,
    service_order,
    part,
):
    """
    Test if returned inventory parts are not included in service order financial summary.
    """
    service_order_part = reserve_part(
        service_order=service_order,
        part=part,
        user=users["attendant"],
        quantity="2.00",
        unit_price="80.00",
    )

    confirm_service_order_part_usage(
        service_order_part=service_order_part,
    )

    return_used_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse(
            "service_orders:service_order_detail",
            args=[service_order.pk],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "Peças do estoque" in content
    assert "R$ 0,00" in content
    assert "R$ 140,00" in content


@pytest.mark.django_db
def test_service_order_part_total_calculates_discount(users, service_order, part):
    """
    Test service order part total with discount.
    """
    service_order_part = ServiceOrderPart.objects.create(
        service_order=service_order,
        part=part,
        quantity=Decimal("2.00"),
        unit_price=Decimal("80.00"),
        discount=Decimal("15.00"),
        status=ServiceOrderPart.Status.RESERVED,
        created_by=users["attendant"],
    )

    assert service_order_part.subtotal == Decimal("160.00")
    assert service_order_part.total == Decimal("145.00")

