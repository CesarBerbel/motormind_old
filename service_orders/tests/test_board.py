from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def users():
    """
    Create users for board tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="board_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="board_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="board_financial@example.com",
        password="StrongPassword123",
    )

    attendant_group, _created = Group.objects.get_or_create(name="Atendente")
    mechanic_group, _created = Group.objects.get_or_create(name="Mecânico")
    financial_group, _created = Group.objects.get_or_create(name="Financeiro")

    attendant.groups.add(attendant_group)
    mechanic.groups.add(mechanic_group)
    financial.groups.add(financial_group)

    return {
        "attendant": attendant,
        "mechanic": mechanic,
        "financial": financial,
    }


@pytest.fixture
def board_orders(users):
    """
    Create service orders for operational board tests.
    """
    today = timezone.localdate()

    customer = Customer.objects.create(
        name="Cliente Quadro",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="QDR-1234",
        brand="Fiat",
        model="Argo",
    )

    open_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS aberta no quadro",
        description="Descrição da OS aberta.",
        status=ServiceOrder.Status.OPEN,
        expected_delivery_date=today + timedelta(days=2),
    )

    waiting_parts_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS aguardando peças",
        description="Descrição da OS aguardando peças.",
        status=ServiceOrder.Status.WAITING_PARTS,
        expected_delivery_date=today + timedelta(days=3),
    )

    finished_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        title="OS finalizada",
        description="Descrição da OS finalizada.",
        status=ServiceOrder.Status.FINISHED,
        expected_delivery_date=today - timedelta(days=3),
    )

    overdue_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS atrasada",
        description="Descrição da OS atrasada.",
        status=ServiceOrder.Status.IN_PROGRESS,
        expected_delivery_date=today - timedelta(days=1),
    )

    canceled_overdue_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        title="OS cancelada atrasada",
        description="Descrição da OS cancelada atrasada.",
        status=ServiceOrder.Status.CANCELED,
        expected_delivery_date=today - timedelta(days=5),
    )

    return {
        "open_order": open_order,
        "waiting_parts_order": waiting_parts_order,
        "finished_order": finished_order,
        "overdue_order": overdue_order,
        "canceled_overdue_order": canceled_overdue_order,
    }


@pytest.mark.django_db
def test_board_requires_login(client):
    """
    Test if operational board requires login.
    """
    response = client.get(reverse("service_orders:service_order_board"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_attendant_can_access_operational_board(client, users, board_orders):
    """
    Test if attendant can access operational board.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_board"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Quadro da oficina" in content
    assert board_orders["open_order"].title in content
    assert board_orders["waiting_parts_order"].title in content
    assert board_orders["finished_order"].title in content


@pytest.mark.django_db
def test_mechanic_can_access_operational_board(client, users, board_orders):
    """
    Test if mechanic can access operational board.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_board"))

    assert response.status_code == 200
    assert "Quadro da oficina" in response.content.decode()


@pytest.mark.django_db
def test_financial_cannot_access_operational_board(client, users, board_orders):
    """
    Test if financial user cannot access operational board.
    """
    client.login(
        username=users["financial"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_board"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_board_search_filters_orders(client, users, board_orders):
    """
    Test if board search filters service orders.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse("service_orders:service_order_board"),
        {
            "search": "aguardando peças",
        },
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert board_orders["waiting_parts_order"].title in content
    assert board_orders["open_order"].title not in content


@pytest.mark.django_db
def test_board_mechanic_filter(client, users, board_orders):
    """
    Test if board can filter by assigned mechanic.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse("service_orders:service_order_board"),
        {
            "mechanic": users["mechanic"].pk,
        },
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert board_orders["open_order"].title in content
    assert board_orders["waiting_parts_order"].title in content
    assert board_orders["finished_order"].title not in content


@pytest.mark.django_db
def test_board_overdue_filter_only_shows_overdue_active_orders(
    client,
    users,
    board_orders,
):
    """
    Test if overdue filter only shows active overdue service orders.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse("service_orders:service_order_board"),
        {
            "overdue": "1",
        },
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert board_orders["overdue_order"].title in content
    assert board_orders["open_order"].title not in content
    assert board_orders["waiting_parts_order"].title not in content
    assert board_orders["finished_order"].title not in content
    assert board_orders["canceled_overdue_order"].title not in content
    assert "Atrasada" in content
