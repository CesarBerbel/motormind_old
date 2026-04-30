import pytest

from customers.forms import CustomerForm, VehicleForm
from customers.models import Customer


@pytest.mark.django_db
def test_customer_form_valid_data():
    """
    Test customer form with valid data.
    """
    form = CustomerForm(
        data={
            "name": "Cliente Teste",
            "phone": "+351 910 000 000",
            "email": "cliente@example.com",
            "document": "123456789",
            "address": "Rua Teste",
            "notes": "Cliente importante",
            "is_active": "on",
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_customer_form_invalid_phone():
    """
    Test customer form with invalid phone.
    """
    form = CustomerForm(
        data={
            "name": "Cliente Teste",
            "phone": "telefone-invalido-abc",
            "email": "cliente@example.com",
            "is_active": "on",
        }
    )

    assert not form.is_valid()
    assert "phone" in form.errors


@pytest.mark.django_db
def test_vehicle_form_normalizes_plate():
    """
    Test if vehicle form normalizes plate to uppercase.
    """
    customer = Customer.objects.create(
        name="Cliente Teste",
        phone="+351 910 000 000",
    )

    form = VehicleForm(
        data={
            "customer": customer.pk,
            "plate": "aa-00-aa",
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "color": "Preto",
            "chassis_number": "",
            "mileage": 10000,
            "notes": "",
            "is_active": "on",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data["plate"] == "AA-00-AA"


@pytest.mark.django_db
def test_vehicle_form_valid_data():
    """
    Test vehicle form with valid data.
    """
    customer = Customer.objects.create(
        name="Cliente Teste",
        phone="+351 910 000 000",
    )

    form = VehicleForm(
        data={
            "customer": customer.pk,
            "plate": "CC-22-CC",
            "brand": "BMW",
            "model": "320d",
            "year": 2022,
            "color": "Branco",
            "chassis_number": "ABC123",
            "mileage": 25000,
            "notes": "Veículo em bom estado",
            "is_active": "on",
        }
    )

    assert form.is_valid()
