import pytest
from model_bakery import baker

from customers.models import Customer, Vehicle


@pytest.fixture
def customer(db):
    return baker.make(
        Customer,
        name="Cliente Teste",
        phone="11999999999",
        email="cliente@test.com",
        document="12345678900",
        is_active=True,
    )


@pytest.fixture
def vehicle(db, customer):
    return baker.make(
        Vehicle,
        customer=customer,
        plate="ABC1234",
        brand="Ford",
        model="Fiesta",
        year=2020,
        mileage=10000,
        is_active=True,
    )
