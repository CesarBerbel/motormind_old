from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from service_orders.forms import (
    BRLDecimalField,
    ServiceOrderForm,
    ServiceOrderTechnicalForm,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def service_order_base_data():
    """
    Create base data for service order form tests.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="attendant@example.com",
        password="StrongPassword123",
    )

    customer = Customer.objects.create(
        name="Cliente Teste",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="ABC-1234",
        brand="Toyota",
        model="Corolla",
    )

    return {
        "user": user,
        "customer": customer,
        "vehicle": vehicle,
    }


def test_brl_decimal_field_accepts_currency_format():
    """
    Test if BRL field accepts formatted Brazilian currency.
    """
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("R$ 1.234,56") == Decimal("1234.56")


def test_brl_decimal_field_accepts_comma_decimal():
    """
    Test if BRL field accepts comma decimal format.
    """
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("150,00") == Decimal("150.00")


def test_brl_decimal_field_accepts_dot_decimal():
    """
    Test if BRL field accepts regular decimal format.
    """
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("150.00") == Decimal("150.00")


@pytest.mark.django_db
def test_service_order_form_valid_data(service_order_base_data):
    """
    Test service order form with valid Brazilian money data.
    """
    customer = service_order_base_data["customer"]
    vehicle = service_order_base_data["vehicle"]

    form = ServiceOrderForm(
        data={
            "customer": customer.pk,
            "vehicle": vehicle.pk,
            "title": "Troca de óleo",
            "description": "Trocar óleo e filtro.",
            "diagnosis": "",
            "solution": "",
            "status": ServiceOrder.Status.OPEN,
            "labor_cost": "R$ 30,00",
            "parts_cost": "R$ 20,00",
            "discount": "R$ 0,00",
            "expected_delivery_date": "",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data["labor_cost"] == Decimal("30.00")
    assert form.cleaned_data["parts_cost"] == Decimal("20.00")
    assert form.cleaned_data["discount"] == Decimal("0.00")


@pytest.mark.django_db
def test_service_order_form_rejects_vehicle_from_other_customer(
    service_order_base_data,
):
    """
    Test if form rejects a vehicle that does not belong to selected customer.
    """
    customer = service_order_base_data["customer"]

    other_customer = Customer.objects.create(
        name="Outro Cliente",
        phone="+55 11 98888-8888",
    )

    other_vehicle = Vehicle.objects.create(
        customer=other_customer,
        plate="XYZ-9876",
        brand="Ford",
        model="Focus",
    )

    form = ServiceOrderForm(
        data={
            "customer": customer.pk,
            "vehicle": other_vehicle.pk,
            "title": "Teste",
            "description": "Teste de validação.",
            "diagnosis": "",
            "solution": "",
            "status": ServiceOrder.Status.OPEN,
            "labor_cost": "R$ 0,00",
            "parts_cost": "R$ 0,00",
            "discount": "R$ 0,00",
            "expected_delivery_date": "",
        }
    )

    assert not form.is_valid()
    assert "vehicle" in form.errors


@pytest.mark.django_db
def test_service_order_technical_form_valid_data(service_order_base_data):
    """
    Test technical form with valid data.
    """
    order = ServiceOrder.objects.create(
        customer=service_order_base_data["customer"],
        vehicle=service_order_base_data["vehicle"],
        created_by=service_order_base_data["user"],
        title="Falha no motor",
        description="Motor falhando.",
    )

    form = ServiceOrderTechnicalForm(
        data={
            "diagnosis": "Velas com desgaste.",
            "solution": "Velas substituídas.",
            "status": ServiceOrder.Status.FINISHED,
        },
        instance=order,
    )

    assert form.is_valid()
