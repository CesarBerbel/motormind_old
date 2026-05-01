import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderNote


@pytest.fixture
def users():
    """
    Create users for note tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="note_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="note_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="note_financial@example.com",
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
def service_order(users):
    """
    Create service order for note tests.
    """
    customer = Customer.objects.create(
        name="Cliente Notas",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="NOT-1234",
        brand="Volkswagen",
        model="Gol",
    )

    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        assigned_mechanic=users["mechanic"],
        title="OS com notas",
        description="Teste de notas internas.",
    )


@pytest.mark.django_db
def test_attendant_can_create_service_order_note(client, users, service_order):
    """
    Test if attendant can create internal note.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_note_create",
            args=[service_order.pk],
        ),
        data={
            "note_type": ServiceOrderNote.NoteType.INTERNAL,
            "text": "Cliente pediu prioridade no serviço.",
        },
    )

    assert response.status_code == 302
    assert ServiceOrderNote.objects.filter(
        service_order=service_order,
        created_by=users["attendant"],
        text="Cliente pediu prioridade no serviço.",
    ).exists()


@pytest.mark.django_db
def test_mechanic_can_create_technical_note(client, users, service_order):
    """
    Test if mechanic can create technical note.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_note_create",
            args=[service_order.pk],
        ),
        data={
            "note_type": ServiceOrderNote.NoteType.TECHNICAL,
            "text": "Foi identificado vazamento no radiador.",
        },
    )

    assert response.status_code == 302
    assert ServiceOrderNote.objects.filter(
        service_order=service_order,
        created_by=users["mechanic"],
        note_type=ServiceOrderNote.NoteType.TECHNICAL,
    ).exists()


@pytest.mark.django_db
def test_financial_cannot_create_service_order_note(client, users, service_order):
    """
    Test if financial user cannot create internal note.
    """
    client.login(
        username=users["financial"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_note_create",
            args=[service_order.pk],
        ),
        data={
            "note_type": ServiceOrderNote.NoteType.INTERNAL,
            "text": "Tentativa sem permissão.",
        },
    )

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
    assert not ServiceOrderNote.objects.filter(
        service_order=service_order,
        text="Tentativa sem permissão.",
    ).exists()


@pytest.mark.django_db
def test_canceled_service_order_does_not_accept_note(client, users, service_order):
    """
    Test if canceled service order cannot receive notes.
    """
    service_order.status = ServiceOrder.Status.CANCELED
    service_order.save()

    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_note_create",
            args=[service_order.pk],
        ),
        data={
            "note_type": ServiceOrderNote.NoteType.INTERNAL,
            "text": "Nota em OS cancelada.",
        },
    )

    assert response.status_code == 302
    assert not ServiceOrderNote.objects.filter(
        service_order=service_order,
        text="Nota em OS cancelada.",
    ).exists()