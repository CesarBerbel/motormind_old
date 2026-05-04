import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


@pytest.fixture
def users():
    """
    Create users for time tracking tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="time_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="time_mechanic@example.com",
        password="StrongPassword123",
    )

    other_mechanic = User.objects.create_user(
        email="time_other_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="time_financial@example.com",
        password="StrongPassword123",
    )

    attendant_group, _created = Group.objects.get_or_create(name="Atendente")
    mechanic_group, _created = Group.objects.get_or_create(name="Mecânico")
    financial_group, _created = Group.objects.get_or_create(name="Financeiro")

    attendant.groups.add(attendant_group)
    mechanic.groups.add(mechanic_group)
    other_mechanic.groups.add(mechanic_group)
    financial.groups.add(financial_group)

    return {
        "attendant": attendant,
        "mechanic": mechanic,
        "other_mechanic": other_mechanic,
        "financial": financial,
    }


@pytest.fixture
def service_order(users):
    """
    Create service order for time tracking tests.
    """
    customer = Customer.objects.create(
        name="Cliente Tempo",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="TMP-1234",
        brand="Fiat",
        model="Strada",
    )

    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS controle de tempo",
        description="Teste de controle de tempo.",
        status=ServiceOrder.Status.IN_PROGRESS,
        priority=ServiceOrder.Priority.HIGH,
    )


@pytest.mark.django_db
def test_mechanic_can_start_time_entry(client, users, service_order):
    """
    Test if mechanic can start a time entry.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_start",
            args=[service_order.pk],
        )
    )

    assert response.status_code == 302
    assert ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
        mechanic=users["mechanic"],
        ended_at__isnull=True,
    ).exists()


@pytest.mark.django_db
def test_mechanic_cannot_start_two_open_entries(client, users, service_order):
    """
    Test if mechanic cannot start two open entries for same service order.
    """
    ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at="2026-05-01T10:00:00Z",
    )

    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_start",
            args=[service_order.pk],
        )
    )

    assert response.status_code == 302
    assert (
        ServiceOrderTimeEntry.objects.filter(
            service_order=service_order,
            mechanic=users["mechanic"],
            ended_at__isnull=True,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_mechanic_can_finish_own_time_entry(client, users, service_order):
    """
    Test if mechanic can finish own time entry.
    """
    entry = ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at="2026-05-01T10:00:00Z",
    )

    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_finish",
            args=[
                service_order.pk,
                entry.pk,
            ],
        ),
        data={
            "note": "Troca de peça concluída.",
        },
    )

    entry.refresh_from_db()

    assert response.status_code == 302
    assert entry.ended_at is not None
    assert entry.note == "Troca de peça concluída."


@pytest.mark.django_db
def test_mechanic_cannot_finish_other_mechanic_entry(client, users, service_order):
    """
    Test if mechanic cannot finish another mechanic time entry.
    """
    entry = ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at="2026-05-01T10:00:00Z",
    )

    client.login(
        username=users["other_mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_finish",
            args=[
                service_order.pk,
                entry.pk,
            ],
        ),
        data={
            "note": "Tentativa indevida.",
        },
    )

    entry.refresh_from_db()

    assert response.status_code == 302
    assert entry.ended_at is None


@pytest.mark.django_db
def test_financial_cannot_start_time_entry(client, users, service_order):
    """
    Test if financial user cannot start time tracking.
    """
    client.login(
        username=users["financial"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_start",
            args=[service_order.pk],
        )
    )

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
    assert not ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
        mechanic=users["financial"],
    ).exists()


@pytest.mark.django_db
def test_canceled_service_order_cannot_start_time(client, users, service_order):
    """
    Test if canceled service order cannot receive time tracking.
    """
    service_order.status = ServiceOrder.Status.CANCELED
    service_order.save()

    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_start",
            args=[service_order.pk],
        )
    )

    assert response.status_code == 302
    assert not ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
    ).exists()


@pytest.mark.django_db
def test_superuser_can_finish_any_time_entry(client, users, service_order):
    """
    Superuser must be able to finish any time entry.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    superuser = User.objects.create_superuser(
        email="super@example.com",
        password="StrongPassword123",
    )

    entry = ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=users["mechanic"],
        started_at="2026-05-01T10:00:00Z",
    )

    client.login(
        username=superuser.email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_finish",
            args=[service_order.pk, entry.pk],
        ),
        data={"note": "Encerrado por superuser"},
    )

    entry.refresh_from_db()

    assert response.status_code == 302
    assert entry.ended_at is not None


@pytest.mark.django_db
def test_mechanic_cannot_start_open_entry_when_has_open_entry_in_another_order(
    client,
    users,
    service_order,
):
    """
    Test if mechanic cannot keep more than one open time entry across all orders.
    """
    other_customer = Customer.objects.create(
        name="Cliente Outra OS",
        phone="+55 11 98888-7777",
    )
    other_vehicle = Vehicle.objects.create(
        customer=other_customer,
        plate="OUT-1234",
        brand="Volkswagen",
        model="Gol",
    )
    other_order = ServiceOrder.objects.create(
        customer=other_customer,
        vehicle=other_vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="Outra OS em execução",
        description="Outra OS para validar trava global de tempo.",
        status=ServiceOrder.Status.IN_PROGRESS,
        priority=ServiceOrder.Priority.MEDIUM,
    )

    ServiceOrderTimeEntry.objects.create(
        service_order=other_order,
        mechanic=users["mechanic"],
        started_at="2026-05-01T10:00:00Z",
    )

    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_time_start",
            args=[service_order.pk],
        )
    )

    assert response.status_code == 302
    assert (
        ServiceOrderTimeEntry.objects.filter(
            mechanic=users["mechanic"],
            ended_at__isnull=True,
        ).count()
        == 1
    )
    assert not ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
        mechanic=users["mechanic"],
        ended_at__isnull=True,
    ).exists()
