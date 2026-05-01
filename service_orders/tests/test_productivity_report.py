from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


@pytest.fixture
def users():
    """
    Create users for productivity report tests.
    """
    User = get_user_model()

    admin = User.objects.create_user(
        email="report_admin@example.com",
        password="StrongPassword123",
    )

    attendant = User.objects.create_user(
        email="report_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="report_mechanic@example.com",
        password="StrongPassword123",
    )

    other_mechanic = User.objects.create_user(
        email="report_other_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="report_financial@example.com",
        password="StrongPassword123",
    )

    admin_group, _created = Group.objects.get_or_create(name="Administrador")
    attendant_group, _created = Group.objects.get_or_create(name="Atendente")
    mechanic_group, _created = Group.objects.get_or_create(name="Mecânico")
    financial_group, _created = Group.objects.get_or_create(name="Financeiro")

    admin.groups.add(admin_group)
    attendant.groups.add(attendant_group)
    mechanic.groups.add(mechanic_group)
    other_mechanic.groups.add(mechanic_group)
    financial.groups.add(financial_group)

    return {
        "admin": admin,
        "attendant": attendant,
        "mechanic": mechanic,
        "other_mechanic": other_mechanic,
        "financial": financial,
    }


@pytest.fixture
def productivity_data(users):
    """
    Create service orders and time entries for productivity report tests.
    """
    now = timezone.now()

    customer = Customer.objects.create(
        name="Cliente Produtividade",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="PRD-1234",
        brand="Fiat",
        model="Pulse",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS produtividade",
        description="Teste de produtividade.",
        status=ServiceOrder.Status.FINISHED,
        priority=ServiceOrder.Priority.HIGH,
        expected_delivery_date=timezone.localdate(),
    )

    other_service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["other_mechanic"],
        title="OS outro mecânico",
        description="Teste de outro mecânico.",
        status=ServiceOrder.Status.FINISHED,
        priority=ServiceOrder.Priority.MEDIUM,
        expected_delivery_date=timezone.localdate(),
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at=now - timedelta(hours=2),
        ended_at=now - timedelta(hours=1),
        note="Primeira hora.",
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at=now - timedelta(minutes=50),
        ended_at=now - timedelta(minutes=20),
        note="Mais meia hora.",
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=other_service_order,
        mechanic=users["other_mechanic"],
        started_at=now - timedelta(hours=3),
        ended_at=now - timedelta(hours=2),
        note="Outro mecânico.",
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at=now - timedelta(minutes=10),
        ended_at=None,
        note="Aberto não deve entrar.",
    )

    return {
        "service_order": service_order,
        "other_service_order": other_service_order,
    }


@pytest.mark.django_db
def test_productivity_report_requires_login(client):
    """
    Test if productivity report requires login.
    """
    response = client.get(reverse("service_orders:mechanic_productivity_report"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_admin_can_access_productivity_report(client, users, productivity_data):
    """
    Test if administrator can access productivity report.
    """
    client.login(
        username=users["admin"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:mechanic_productivity_report"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Produtividade por mecânico" in content
    assert users["mechanic"].email in content
    assert users["other_mechanic"].email in content
    assert productivity_data["service_order"].title in content


@pytest.mark.django_db
def test_attendant_can_access_productivity_report(client, users, productivity_data):
    """
    Test if attendant can access productivity report.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:mechanic_productivity_report"))

    assert response.status_code == 200
    assert "Produtividade por mecânico" in response.content.decode()


@pytest.mark.django_db
def test_mechanic_cannot_access_productivity_report(client, users, productivity_data):
    """
    Test if mechanic cannot access productivity report.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:mechanic_productivity_report"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_financial_cannot_access_productivity_report(client, users, productivity_data):
    """
    Test if financial user cannot access productivity report.
    """
    client.login(
        username=users["financial"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:mechanic_productivity_report"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_productivity_report_filters_by_mechanic(client, users, productivity_data):
    """
    Test if productivity report filters by mechanic.
    """
    client.login(
        username=users["admin"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse("service_orders:mechanic_productivity_report"),
        {
            "mechanic": users["mechanic"].pk,
        },
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert users["mechanic"].email in content
    assert productivity_data["service_order"].title in content
    assert productivity_data["other_service_order"].title not in content


@pytest.mark.django_db
def test_productivity_report_ignores_open_entries(client, users, productivity_data):
    """
    Test if productivity report ignores open time entries.
    """
    client.login(
        username=users["admin"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:mechanic_productivity_report"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Apontamentos encerrados" in content
    assert "3" in content
