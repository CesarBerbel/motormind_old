from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


@pytest.fixture
def mechanic_group():
    """
    Return the mechanic group used by role-based access control.
    """
    group, _created = Group.objects.get_or_create(name="Mecânico")
    return group


@pytest.fixture
def attendant_group():
    """
    Return the attendant group used to verify denied access.
    """
    group, _created = Group.objects.get_or_create(name="Atendente")
    return group


@pytest.fixture
def mechanic_user(mechanic_group):
    """
    Create a mechanic user.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="mechanic_area@example.com",
        password="StrongPassword123",
    )
    user.groups.add(mechanic_group)

    return user


@pytest.fixture
def other_mechanic_user(mechanic_group):
    """
    Create another mechanic user to verify data isolation in the panel.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="other_mechanic_area@example.com",
        password="StrongPassword123",
    )
    user.groups.add(mechanic_group)

    return user


@pytest.fixture
def attendant_user(attendant_group):
    """
    Create an attendant user that should not access the mechanic area.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="attendant_mechanic_area@example.com",
        password="StrongPassword123",
    )
    user.groups.add(attendant_group)

    return user


@pytest.fixture
def service_order_data(attendant_user, mechanic_user):
    """
    Create customer and vehicle base data for mechanic area tests.
    """
    customer = Customer.objects.create(
        name="Cliente Painel Mecânico",
        phone="+55 11 98888-7777",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="MEC-1234",
        brand="Volkswagen",
        model="Gol",
    )

    return {
        "customer": customer,
        "vehicle": vehicle,
        "created_by": attendant_user,
        "mechanic": mechanic_user,
    }


def create_service_order(*, title, mechanic, service_order_data, **kwargs):
    """
    Create a service order with sensible defaults for tests.
    """
    defaults = {
        "customer": service_order_data["customer"],
        "vehicle": service_order_data["vehicle"],
        "created_by": service_order_data["created_by"],
        "assigned_mechanic": mechanic,
        "title": title,
        "description": "Descrição da OS para teste do painel do mecânico.",
        "status": ServiceOrder.Status.IN_PROGRESS,
        "priority": ServiceOrder.Priority.MEDIUM,
    }
    defaults.update(kwargs)

    return ServiceOrder.objects.create(**defaults)


@pytest.mark.django_db
def test_mechanic_area_requires_login(client):
    """
    Anonymous users must be redirected to login before accessing mechanic area.
    """
    response = client.get(reverse("accounts:mechanic_area"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_only_mechanic_group_can_access_mechanic_area(client, attendant_user):
    """
    Users outside the mechanic group must not access the mechanic area.
    """
    client.login(
        username=attendant_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:mechanic_area"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_mechanic_area_lists_only_active_orders_assigned_to_current_mechanic(
    client,
    mechanic_user,
    other_mechanic_user,
    service_order_data,
):
    """
    The panel must show only active service orders assigned to the logged mechanic.
    """
    own_order = create_service_order(
        title="Troca de embreagem",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
    )
    create_service_order(
        title="OS finalizada não deve aparecer",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
        status=ServiceOrder.Status.FINISHED,
    )
    create_service_order(
        title="OS de outro mecânico não deve aparecer",
        mechanic=other_mechanic_user,
        service_order_data=service_order_data,
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:mechanic_area"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Área do mecânico" in content
    assert own_order.title in content
    assert "OS finalizada não deve aparecer" not in content
    assert "OS de outro mecânico não deve aparecer" not in content


@pytest.mark.django_db
def test_mechanic_area_filters_assigned_orders_by_status_priority_and_search(
    client,
    mechanic_user,
    service_order_data,
):
    """
    The mechanic can filter their own active orders by search, status and priority.
    """
    matching_order = create_service_order(
        title="Diagnóstico freio dianteiro",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
        status=ServiceOrder.Status.WAITING_PARTS,
        priority=ServiceOrder.Priority.HIGH,
    )
    create_service_order(
        title="Revisão elétrica",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
        status=ServiceOrder.Status.IN_PROGRESS,
        priority=ServiceOrder.Priority.LOW,
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse("accounts:mechanic_area"),
        {
            "search": "freio",
            "status": ServiceOrder.Status.WAITING_PARTS,
            "priority": ServiceOrder.Priority.HIGH,
        },
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert matching_order.title in content
    assert "Revisão elétrica" not in content
    assert "Exibindo 1 ordem(ns)" in content


@pytest.mark.django_db
def test_mechanic_area_shows_overdue_counter_and_open_time_entry(
    client,
    mechanic_user,
    service_order_data,
):
    """
    The panel must show overdue counter and current open time entry when present.
    """
    today = timezone.localdate()
    order = create_service_order(
        title="OS atrasada com tempo aberto",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
        expected_delivery_date=today - timedelta(days=1),
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=order,
        mechanic=mechanic_user,
        started_at=timezone.now() - timedelta(hours=2),
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:mechanic_area"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Minhas OS atrasadas" in content
    assert "Existe um apontamento aberto" in content
    assert "Continuar apontamento" in content


@pytest.mark.django_db
def test_mechanic_area_shows_quick_action_buttons(
    client,
    mechanic_user,
    service_order_data,
):
    """
    The mechanic panel must expose quick links and time tracking actions.
    """
    order = create_service_order(
        title="OS com ações rápidas",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:mechanic_area"))
    content = response.content.decode()

    assert response.status_code == 200
    assert (
        reverse("service_orders:service_order_detail", kwargs={"pk": order.pk})
        in content
    )
    assert (
        reverse(
            "service_orders:service_order_technical_update", kwargs={"pk": order.pk}
        )
        in content
    )
    assert (
        reverse("service_orders:service_order_time_start", kwargs={"pk": order.pk})
        in content
    )
    assert "Iniciar tempo" in content
    assert "Técnico" in content


@pytest.mark.django_db
def test_mechanic_can_start_time_from_quick_action(
    client,
    mechanic_user,
    service_order_data,
):
    """
    Posting to the quick start action must create an open time entry.
    """
    order = create_service_order(
        title="OS para iniciar tempo",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse("service_orders:service_order_time_start", kwargs={"pk": order.pk}),
        follow=True,
    )

    assert response.status_code == 200
    assert ServiceOrderTimeEntry.objects.filter(
        service_order=order,
        mechanic=mechanic_user,
        ended_at__isnull=True,
    ).exists()


@pytest.mark.django_db
def test_mechanic_can_finish_time_from_quick_action(
    client,
    mechanic_user,
    service_order_data,
):
    """
    Posting to the quick finish action must close the open time entry.
    """
    order = create_service_order(
        title="OS para finalizar tempo",
        mechanic=mechanic_user,
        service_order_data=service_order_data,
    )
    entry = ServiceOrderTimeEntry.objects.create(
        service_order=order,
        mechanic=mechanic_user,
        started_at=timezone.now() - timedelta(hours=1),
    )

    client.login(
        username=mechanic_user.email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_finish",
            kwargs={
                "pk": order.pk,
                "entry_pk": entry.pk,
            },
        ),
        {
            "note": "Serviço conferido e apontamento encerrado pelo painel.",
        },
        follow=True,
    )

    entry.refresh_from_db()

    assert response.status_code == 200
    assert entry.ended_at is not None
    assert entry.note == "Serviço conferido e apontamento encerrado pelo painel."
