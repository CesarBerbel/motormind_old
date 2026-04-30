import pytest
from django.db import IntegrityError

from customers.models import Customer, Vehicle


@pytest.mark.django_db
def test_customer_string_representation():
    """
    Test customer string representation.
    """
    customer = Customer.objects.create(
        name="João Silva",
        phone="+351 910 000 000",
    )

    assert str(customer) == "João Silva"


@pytest.mark.django_db
def test_vehicle_string_representation():
    """
    Test vehicle string representation.
    """
    customer = Customer.objects.create(
        name="Maria Santos",
        phone="+351 920 000 000",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )

    assert str(vehicle) == "AA-00-AA - Toyota Corolla"


@pytest.mark.django_db
def test_vehicle_plate_must_be_unique():
    """
    Test if vehicle plate unique constraint works.
    """
    customer = Customer.objects.create(
        name="Carlos Lima",
        phone="+351 930 000 000",
    )

    Vehicle.objects.create(
        customer=customer,
        plate="BB-11-BB",
        brand="Ford",
        model="Focus",
    )

    with pytest.raises(IntegrityError):
        Vehicle.objects.create(
            customer=customer,
            plate="BB-11-BB",
            brand="Ford",
            model="Fiesta",
        )
