from decimal import Decimal

import pytest

from inventory.forms import BRLDecimalField, PartForm, ServiceOrderPartForm
from inventory.models import Part


def test_brl_decimal_field_accepts_formatted_brl_value():
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("R$ 1.234,56") == Decimal("1234.56")


def test_brl_decimal_field_accepts_comma_decimal_value():
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("150,00") == Decimal("150.00")


def test_brl_decimal_field_accepts_dot_decimal_value():
    field = BRLDecimalField(max_digits=10, decimal_places=2)

    assert field.clean("150.00") == Decimal("150.00")


@pytest.mark.django_db
def test_part_form_accepts_money_mask_values():
    form = PartForm(
        data={
            "name": "Pastilha de freio",
            "internal_code": "BRK-FORM-001",
            "barcode": "",
            "brand": "Bosch",
            "category": "Freio",
            "unit": "un",
            "cost_price": "R$ 80,00",
            "sale_price": "R$ 150,00",
            "current_stock": "10.00",
            "minimum_stock": "3.00",
            "location": "Prateleira A1",
            "is_active": "on",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data["cost_price"] == Decimal("80.00")
    assert form.cleaned_data["sale_price"] == Decimal("150.00")


@pytest.mark.django_db
def test_part_form_rejects_negative_cost_price():
    form = PartForm(
        data={
            "name": "Peça inválida",
            "internal_code": "INVALID-COST-001",
            "barcode": "",
            "brand": "",
            "category": "",
            "unit": "un",
            "cost_price": "-1.00",
            "sale_price": "10.00",
            "current_stock": "1.00",
            "minimum_stock": "1.00",
            "location": "",
            "is_active": "on",
        }
    )

    assert not form.is_valid()
    assert "cost_price" in form.errors


@pytest.mark.django_db
def test_service_order_part_form_accepts_money_mask_values():
    part = Part.objects.create(
        name="Filtro de óleo",
        internal_code="FLT-FORM-001",
        cost_price=Decimal("30.00"),
        sale_price=Decimal("60.00"),
        current_stock=Decimal("5.00"),
        minimum_stock=Decimal("2.00"),
    )

    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "R$ 60,00",
            "discount": "R$ 10,00",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data["unit_price"] == Decimal("60.00")
    assert form.cleaned_data["discount"] == Decimal("10.00")


@pytest.mark.django_db
def test_service_order_part_form_rejects_discount_greater_than_subtotal():
    part = Part.objects.create(
        name="Filtro de ar",
        internal_code="AIR-FORM-001",
        cost_price=Decimal("20.00"),
        sale_price=Decimal("40.00"),
        current_stock=Decimal("5.00"),
        minimum_stock=Decimal("2.00"),
    )

    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "1.00",
            "unit_price": "R$ 40,00",
            "discount": "R$ 50,00",
        }
    )

    assert not form.is_valid()
