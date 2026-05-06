from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from inventory.models import Part, PartBrand, PartCategory, StockMovement


@pytest.fixture
def users():
    """
    Create users for inventory view tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="inventory_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="inventory_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="inventory_financial@example.com",
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
def part():
    """
    Create part for inventory view tests.
    """
    brand, _ = PartBrand.objects.get_or_create(name="Bosch")
    category = PartCategory.objects.get_or_create(name="Freio")[0]

    return Part.objects.create(
        name="Pastilha de freio",
        internal_code="BRK-VIEW-001",
        brand=brand,
        category=category,
        unit="un",
        cost_price=Decimal("80.00"),
        sale_price=Decimal("150.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("3.00"),
        location="Prateleira A1",
    )


@pytest.mark.django_db
def test_part_list_requires_login(client):
    """
    Test if part list requires login.
    """
    response = client.get(reverse("inventory:part_list"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_attendant_can_access_part_list(client, users, part):
    """
    Test if attendant can access inventory list.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("inventory:part_list"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Estoque" in content
    assert part.name in content


@pytest.mark.django_db
def test_mechanic_can_access_part_list(client, users, part):
    """
    Test if mechanic can access inventory list.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("inventory:part_list"))

    assert response.status_code == 200
    assert part.name in response.content.decode()


@pytest.mark.django_db
def test_financial_can_access_part_list(client, users, part):
    """
    Test if financial can access inventory list.
    """
    client.login(
        username=users["financial"].email,
        password="StrongPassword123",
    )

    response = client.get(reverse("inventory:part_list"))

    assert response.status_code == 200
    assert part.name in response.content.decode()


@pytest.mark.django_db
def test_attendant_can_create_part(client, users):
    """
    Test if attendant can create part.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse("inventory:part_create"),
        data={
            "name": "Filtro de óleo",
            "internal_code": "FLT-VIEW-001",
            "barcode": "",
            "brand": "Mann",
            "category": "Motor",
            "unit": "un",
            "cost_price": "30.00",
            "sale_price": "60.00",
            "current_stock": "5.00",
            "minimum_stock": "2.00",
            "location": "Prateleira B1",
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    assert Part.objects.filter(internal_code="FLT-VIEW-001").exists()


@pytest.mark.django_db
def test_mechanic_cannot_create_part(client, users):
    """
    Test if mechanic cannot create part.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse("inventory:part_create"),
        data={
            "name": "Peça bloqueada",
            "internal_code": "BLOCK-001",
            "cost_price": "1.00",
            "sale_price": "2.00",
            "current_stock": "1.00",
            "minimum_stock": "1.00",
            "unit": "un",
        },
    )

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
    assert not Part.objects.filter(internal_code="BLOCK-001").exists()


@pytest.mark.django_db
def test_attendant_can_create_stock_entry(client, users, part):
    """
    Test if attendant can create stock entry.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "inventory:stock_movement_create",
            args=[part.pk],
        ),
        data={
            "movement_type": "in",
            "quantity": "5.00",
            "reason": "Entrada de compra.",
        },
    )

    part.refresh_from_db()

    assert response.status_code == 302
    assert part.current_stock == Decimal("15.00")
    assert StockMovement.objects.filter(
        part=part,
        movement_type=StockMovement.MovementType.IN,
    ).exists()


@pytest.mark.django_db
def test_stock_output_blocks_insufficient_stock(client, users, part):
    """
    Test if stock output blocks insufficient stock.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "inventory:stock_movement_create",
            args=[part.pk],
        ),
        data={
            "movement_type": "out",
            "quantity": "50.00",
            "reason": "Saída inválida.",
        },
    )

    part.refresh_from_db()

    assert response.status_code == 200
    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_mechanic_cannot_create_stock_movement(client, users, part):
    """
    Test if mechanic cannot create stock movement.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "inventory:stock_movement_create",
            args=[part.pk],
        ),
        data={
            "movement_type": "in",
            "quantity": "5.00",
            "reason": "Tentativa sem permissão.",
        },
    )

    part.refresh_from_db()

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
    assert part.current_stock == Decimal("10.00")
