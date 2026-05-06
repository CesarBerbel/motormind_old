from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse

from customers.models import Customer, Vehicle
from inventory.forms import ServiceOrderPartForm
from inventory.models import (
    Part,
    PartBrand,
    PartCategory,
    PurchaseOrder,
    ServiceOrderPart,
    StockMovement,
)
from inventory.services import (
    cancel_reserved_service_order_part,
    confirm_service_order_part_usage,
    reserve_part_for_service_order,
    return_used_service_order_part,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def users():
    """
    Create users for service order inventory tests.
    """
    User = get_user_model()

    attendant = User.objects.create_user(
        email="inventory_os_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="inventory_os_mechanic@example.com",
        password="StrongPassword123",
    )

    attendant_group, _created = Group.objects.get_or_create(name="Atendente")
    mechanic_group, _created = Group.objects.get_or_create(name="Mecânico")

    attendant.groups.add(attendant_group)
    mechanic.groups.add(mechanic_group)

    return {
        "attendant": attendant,
        "mechanic": mechanic,
    }


@pytest.fixture
def service_order(users):
    """
    Create service order for inventory integration tests.
    """
    customer = Customer.objects.create(
        name="Cliente Estoque OS",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="EST-1234",
        brand="Fiat",
        model="Uno",
    )

    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=users["attendant"],
        title="OS com peças",
        description="Teste de peças na OS.",
        status=ServiceOrder.Status.OPEN,
        priority=ServiceOrder.Priority.MEDIUM,
    )


@pytest.fixture
def part():
    """
    Create part for service order inventory tests.
    """
    category = PartCategory.objects.get_or_create(name="Freio")[0]
    brand, _ = PartBrand.objects.get_or_create(name="Mann")

    return Part.objects.create(
        name="Filtro de ar",
        internal_code="AIR-OS-001",
        brand=brand,
        category=category,
        unit="un",
        cost_price=Decimal("20.00"),
        sale_price=Decimal("45.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("2.00"),
    )


@pytest.mark.django_db
def test_reserve_part_for_service_order_decreases_stock(service_order, part, users):
    """
    Test if reserving a part for service order decreases stock.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )

    part.refresh_from_db()

    assert service_order_part.status == ServiceOrderPart.Status.RESERVED
    assert part.current_stock == Decimal("8.00")
    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RESERVE,
    ).exists()


@pytest.mark.django_db
def test_reserve_part_opens_purchase_order_when_stock_is_insufficient(
    service_order, part, users
):
    """
    Reservar mais do que o estoque disponível não deve bloquear a OS.
    O sistema reserva o saldo existente e abre pedido de compra para a diferença.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "50.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )

    part.refresh_from_db()

    assert service_order_part.status == ServiceOrderPart.Status.WAITING_PURCHASE
    assert service_order_part.quantity == Decimal("50.00")
    assert service_order_part.reserved_quantity == Decimal("10.00")
    assert part.current_stock == Decimal("0.00")

    purchase_order = PurchaseOrder.objects.get(
        service_order=service_order,
        service_order_part=service_order_part,
        part=part,
    )
    assert purchase_order.requested_quantity == Decimal("40.00")
    assert purchase_order.status == PurchaseOrder.Status.OPEN


@pytest.mark.django_db
def test_confirm_service_order_part_usage_changes_status(service_order, part, users):
    """
    Test if confirming usage changes status without changing stock again.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )

    confirm_service_order_part_usage(service_order_part=service_order_part)

    service_order_part.refresh_from_db()
    part.refresh_from_db()

    assert service_order_part.status == ServiceOrderPart.Status.USED
    assert part.current_stock == Decimal("8.00")


@pytest.mark.django_db
def test_cancel_reserved_service_order_part_releases_stock(service_order, part, users):
    """
    Test if canceling reserved part releases stock.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )

    cancel_reserved_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    service_order_part.refresh_from_db()
    part.refresh_from_db()

    assert service_order_part.status == ServiceOrderPart.Status.CANCELED
    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_return_used_service_order_part_returns_stock(service_order, part, users):
    """
    Test if returning used part increases stock.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )

    confirm_service_order_part_usage(service_order_part=service_order_part)

    return_used_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    service_order_part.refresh_from_db()
    part.refresh_from_db()

    assert service_order_part.status == ServiceOrderPart.Status.RETURNED
    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_attendant_can_add_part_to_service_order(client, service_order, part, users):
    """
    Test if attendant can add part to service order using view.
    """
    client.login(
        username=users["attendant"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "inventory:service_order_part_add",
            args=[service_order.pk],
        ),
        data={
            "part": part.pk,
            "quantity": "1.00",
            "unit_price": "45.00",
            "discount": "0.00",
        },
    )

    part.refresh_from_db()

    assert response.status_code == 302
    assert part.current_stock == Decimal("9.00")
    assert ServiceOrderPart.objects.filter(
        service_order=service_order, part=part
    ).exists()


@pytest.mark.django_db
def test_mechanic_cannot_add_part_to_service_order(client, service_order, part, users):
    """
    Test if mechanic cannot add part to service order.
    """
    client.login(
        username=users["mechanic"].email,
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "inventory:service_order_part_add",
            args=[service_order.pk],
        ),
        data={
            "part": part.pk,
            "quantity": "1.00",
            "unit_price": "45.00",
            "discount": "0.00",
        },
    )

    part.refresh_from_db()

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_return_used_service_order_part_creates_return_movement(
    service_order, part, users
):
    """
    Test if returning a used part records an auditable return movement.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )
    confirm_service_order_part_usage(service_order_part=service_order_part)

    return_used_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RETURN,
        quantity=Decimal("2.00"),
    ).exists()


@pytest.mark.django_db
def test_return_used_service_order_part_blocks_duplicate_return(
    service_order, part, users
):
    """
    Test if a returned part cannot be returned twice.
    """
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": "2.00",
            "unit_price": "45.00",
            "discount": "0.00",
        }
    )

    assert form.is_valid()

    service_order_part = reserve_part_for_service_order(
        service_order=service_order,
        form=form,
        created_by=users["attendant"],
    )
    confirm_service_order_part_usage(service_order_part=service_order_part)

    returned_part = return_used_service_order_part(
        service_order_part=service_order_part,
        changed_by=users["attendant"],
    )

    with pytest.raises(ValidationError):
        return_used_service_order_part(
            service_order_part=returned_part,
            changed_by=users["attendant"],
        )

    part.refresh_from_db()

    assert part.current_stock == Decimal("10.00")
    assert (
        StockMovement.objects.filter(
            part=part,
            service_order=service_order,
            movement_type=StockMovement.MovementType.RETURN,
        ).count()
        == 1
    )
