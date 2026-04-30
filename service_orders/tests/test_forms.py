import pytest
from django.contrib.auth import get_user_model

from customers.models import Customer, Vehicle
from service_orders.forms import ServiceOrderForm, ServiceOrderTechnicalForm
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
def test_service_order_form_valid_data(service_order_base_data):
    """
    Test service order form with valid data.
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
            "labor_cost": "30.00",
            "parts_cost": "20.00",
            "discount": "0.00",
            "expected_delivery_date": "",
        }
    )

    assert form.is_valid()


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
        phone="+351 920 000 000",
    )

    other_vehicle = Vehicle.objects.create(
        customer=other_customer,
        plate="BB-11-BB",
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
            "labor_cost": "0.00",
            "parts_cost": "0.00",
            "discount": "0.00",
            "expected_delivery_date": "",
        }
    )

    assert not form.is_valid()
    assert "__all__" in form.errors


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
