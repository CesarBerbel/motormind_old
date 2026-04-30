from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def user():
    """
    Create a default authenticated user.
    """
    User = get_user_model()

    return User.objects.create_user(
        email="user@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def attendant_user():
    """
    Create an attendant user.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="attendant_dashboard@example.com",
        password="StrongPassword123",
    )

    group, _created = Group.objects.get_or_create(name="Atendente")
    attendant.groups.add(group)

    return attendant


@pytest.fixture
def mechanic_user():
    """
    Create a mechanic user.
    """
    User = get_user_model()

    mechanic = User.objects.create_user(
        email="mechanic_dashboard@example.com",
        password="StrongPassword123",
    )

    group, _created = Group.objects.get_or_create(name="Mecânico")
    mechanic.groups.add(group)

    return mechanic


@pytest.fixture
def service_order_base_data(attendant_user, mechanic_user):
    """
    Create base data for service order dashboard tests.
    """
    customer = Customer.objects.create(
        name="Cliente Dashboard",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="DSH-1234",
        brand="Fiat",
        model="Uno",
    )

    return {
        "user": attendant_user,
        "mechanic": mechanic_user,
        "customer": customer,
        "vehicle": vehicle,
    }


@pytest.mark.django_db
def test_login_page_loads(client):
    """
    Test if login page loads successfully.
    """
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert "Entrar no sistema" in response.content.decode()


@pytest.mark.django_db
def test_register_page_loads(client):
    """
    Test if register page loads successfully.
    """
    response = client.get(reverse("accounts:register"))

    assert response.status_code == 200
    assert "Criar conta" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    """
    Test if dashboard redirects anonymous users.
    """
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_authenticated_user_can_access_dashboard(client, user):
    """
    Test if authenticated user can access dashboard.
    """
    client.login(
        username="user@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert user.email in response.content.decode()


@pytest.mark.django_db
def test_dashboard_shows_overdue_service_order_counter(
    client,
    attendant_user,
    service_order_base_data,
):
    """
    Test if dashboard shows overdue service order counter.
    """
    today = timezone.localdate()

    ServiceOrder.objects.create(
        customer=service_order_base_data["customer"],
        vehicle=service_order_base_data["vehicle"],
        created_by=attendant_user,
        title="OS atrasada",
        description="Ordem atrasada para teste.",
        status=ServiceOrder.Status.IN_PROGRESS,
        expected_delivery_date=today - timedelta(days=1),
    )

    ServiceOrder.objects.create(
        customer=service_order_base_data["customer"],
        vehicle=service_order_base_data["vehicle"],
        created_by=attendant_user,
        title="OS finalizada atrasada",
        description="Ordem finalizada atrasada que não deve contar.",
        status=ServiceOrder.Status.FINISHED,
        expected_delivery_date=today - timedelta(days=3),
    )

    ServiceOrder.objects.create(
        customer=service_order_base_data["customer"],
        vehicle=service_order_base_data["vehicle"],
        created_by=attendant_user,
        title="OS futura",
        description="Ordem futura que não deve contar como atrasada.",
        status=ServiceOrder.Status.OPEN,
        expected_delivery_date=today + timedelta(days=3),
    )

    client.login(
        username=attendant_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Ordens atrasadas" in content
    assert "Ver atrasadas" in content
    assert '<p class="display-6 mb-2">' in content
    assert "1" in content


@pytest.mark.django_db
def test_dashboard_shows_assigned_to_me_counter(
    client,
    attendant_user,
    mechanic_user,
    service_order_base_data,
):
    """
    Test if dashboard shows assigned service orders counter for current user.
    """
    ServiceOrder.objects.create(
        customer=service_order_base_data["customer"],
        vehicle=service_order_base_data["vehicle"],
        created_by=attendant_user,
        assigned_mechanic=mechanic_user,
        title="OS do mecânico",
        description="Ordem atribuída ao mecânico.",
        status=ServiceOrder.Status.IN_PROGRESS,
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Minhas ordens" in content
    assert "Ver minhas ordens" in content
    assert '<p class="display-6 mb-2">' in content
    assert "1" in content
