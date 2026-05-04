import pytest
from django.contrib.auth import get_user_model

from accounts.selectors import (
    get_attendant_dashboard_data,
    get_attendant_quick_search_results,
)
from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def attendant_user():
    """
    Create a user that can be used as service order creator in selector tests.
    """
    User = get_user_model()

    return User.objects.create_user(
        email="selector-attendant@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def customer_with_vehicle():
    """
    Create an active customer with an active vehicle.
    """
    customer = Customer.objects.create(
        name="Maria Atendimento",
        phone="11999999999",
        email="maria@example.com",
        document="12345678901",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="ABC-1234",
        brand="Fiat",
        model="Uno",
    )

    return customer, vehicle


@pytest.mark.django_db
def test_attendant_quick_search_returns_customer_by_name(customer_with_vehicle):
    """
    The quick search should find active customers by name.
    """
    customer, _vehicle = customer_with_vehicle

    result = get_attendant_quick_search_results("Maria")

    assert result["has_query"] is True
    assert list(result["customers"]) == [customer]


@pytest.mark.django_db
def test_attendant_quick_search_returns_vehicle_by_plate(customer_with_vehicle):
    """
    The quick search should find active vehicles by plate.
    """
    _customer, vehicle = customer_with_vehicle

    result = get_attendant_quick_search_results("ABC-1234")

    assert result["has_query"] is True
    assert list(result["vehicles"]) == [vehicle]


@pytest.mark.django_db
def test_attendant_quick_search_ignores_empty_query(customer_with_vehicle):
    """
    Empty searches should not return all customers or vehicles accidentally.
    """
    result = get_attendant_quick_search_results("   ")

    assert result["has_query"] is False
    assert list(result["customers"]) == []
    assert list(result["vehicles"]) == []


@pytest.mark.django_db
def test_attendant_quick_search_ignores_inactive_records(customer_with_vehicle):
    """
    The quick search should only suggest active customers and active vehicles.
    """
    customer, vehicle = customer_with_vehicle
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    vehicle.is_active = False
    vehicle.save(update_fields=["is_active"])

    result = get_attendant_quick_search_results("Maria")

    assert list(result["customers"]) == []
    assert list(result["vehicles"]) == []


@pytest.mark.django_db
def test_attendant_dashboard_data_includes_quick_search_context(
    attendant_user,
    customer_with_vehicle,
):
    """
    The attendant dashboard selector should expose quick search data to the view.
    """
    customer, vehicle = customer_with_vehicle

    ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=attendant_user,
        title="Troca de óleo",
        description="Cliente solicitou revisão básica.",
        status=ServiceOrder.Status.OPEN,
    )

    context = get_attendant_dashboard_data(search_query="ABC")

    assert context["customers_count"] == 1
    assert context["vehicles_count"] == 1
    assert context["open_orders_count"] == 1
    assert context["quick_search"]["query"] == "ABC"
    assert list(context["quick_search"]["vehicles"]) == [vehicle]
