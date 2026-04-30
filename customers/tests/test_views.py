import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle


@pytest.fixture
def create_user_with_group():
    """
    Create a user with a specific group.
    """

    def _create_user_with_group(email, group_name):
        User = get_user_model()

        user = User.objects.create_user(
            email=email,
            password="StrongPassword123",
        )

        group, _created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        return user

    return _create_user_with_group


@pytest.fixture
def customer():
    """
    Create a default customer.
    """
    return Customer.objects.create(
        name="Cliente Teste",
        phone="+351 910 000 000",
    )


@pytest.fixture
def vehicle(customer):
    """
    Create a default vehicle.
    """
    return Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )


@pytest.mark.django_db
def test_customer_list_requires_login(client):
    """
    Test if customer list requires login.
    """
    response = client.get(reverse("customers:customer_list"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_attendant_can_access_customer_list(client, create_user_with_group):
    """
    Test if attendant can access customer list.
    """
    create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("customers:customer_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_mechanic_cannot_access_customer_list(client, create_user_with_group):
    """
    Test if mechanic cannot access customer list.
    """
    create_user_with_group(
        "mechanic@example.com",
        "Mecânico",
    )

    client.login(
        username="mechanic@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("customers:customer_list"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_mechanic_can_access_vehicle_list(client, create_user_with_group):
    """
    Test if mechanic can access vehicle list.
    """
    create_user_with_group(
        "mechanic@example.com",
        "Mecânico",
    )

    client.login(
        username="mechanic@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("customers:vehicle_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_financial_cannot_access_vehicle_list(client, create_user_with_group):
    """
    Test if financial user cannot access vehicle list.
    """
    create_user_with_group(
        "financial@example.com",
        "Financeiro",
    )

    client.login(
        username="financial@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("customers:vehicle_list"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_attendant_can_create_customer(client, create_user_with_group):
    """
    Test if attendant can create a customer.
    """
    create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse("customers:customer_create"),
        data={
            "name": "Novo Cliente",
            "phone": "+351 910 111 222",
            "email": "novo@example.com",
            "document": "123456789",
            "address": "Rua Nova",
            "notes": "",
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    assert Customer.objects.filter(name="Novo Cliente").exists()


@pytest.mark.django_db
def test_attendant_can_create_vehicle(client, create_user_with_group, customer):
    """
    Test if attendant can create a vehicle.
    """
    create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse("customers:vehicle_create"),
        data={
            "customer": customer.pk,
            "plate": "ZZ-99-ZZ",
            "brand": "Renault",
            "model": "Clio",
            "year": 2018,
            "color": "Cinza",
            "chassis_number": "",
            "mileage": 80000,
            "notes": "",
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    assert Vehicle.objects.filter(plate="ZZ-99-ZZ").exists()
