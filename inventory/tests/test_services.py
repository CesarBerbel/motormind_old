from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from inventory.models import Part, StockMovement
from inventory.services import (
    adjust_stock,
    create_stock_entry,
    create_stock_loss,
    create_stock_output,
    release_reserved_stock,
    reserve_stock,
    return_stock,
)


@pytest.fixture
def user():
    """
    Create user for inventory service tests.
    """
    User = get_user_model()

    return User.objects.create_user(
        email="inventory_service_user@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def part():
    """
    Create part for inventory service tests.
    """
    return Part.objects.create(
        name="Filtro de óleo",
        internal_code="FLT-001",
        brand="Mann",
        category="Motor",
        unit="un",
        cost_price=Decimal("30.00"),
        sale_price=Decimal("60.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("2.00"),
        location="Prateleira B1",
    )


@pytest.mark.django_db
def test_create_stock_entry_increases_current_stock(part, user):
    """
    Test if stock entry increases current stock.
    """
    movement = create_stock_entry(
        part=part,
        quantity=Decimal("5.00"),
        created_by=user,
        reason="Entrada de compra.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.IN
    assert part.current_stock == Decimal("15.00")


@pytest.mark.django_db
def test_create_stock_output_decreases_current_stock(part, user):
    """
    Test if stock output decreases current stock.
    """
    movement = create_stock_output(
        part=part,
        quantity=Decimal("3.00"),
        created_by=user,
        reason="Saída manual.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.OUT
    assert part.current_stock == Decimal("7.00")


@pytest.mark.django_db
def test_create_stock_output_blocks_negative_stock(part, user):
    """
    Test if stock output blocks insufficient stock.
    """
    with pytest.raises(ValidationError):
        create_stock_output(
            part=part,
            quantity=Decimal("20.00"),
            created_by=user,
            reason="Saída inválida.",
        )

    part.refresh_from_db()

    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_create_stock_loss_decreases_current_stock(part, user):
    """
    Test if stock loss decreases current stock.
    """
    movement = create_stock_loss(
        part=part,
        quantity=Decimal("2.00"),
        created_by=user,
        reason="Peça danificada.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.LOSS
    assert part.current_stock == Decimal("8.00")


@pytest.mark.django_db
def test_reserve_stock_decreases_current_stock(part, user):
    """
    Test if stock reservation decreases available stock.
    """
    movement = reserve_stock(
        part=part,
        quantity=Decimal("4.00"),
        created_by=user,
        reason="Reserva para OS.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RESERVE
    assert part.current_stock == Decimal("6.00")


@pytest.mark.django_db
def test_release_reserved_stock_increases_current_stock(part, user):
    """
    Test if releasing reserved stock increases current stock.
    """
    movement = release_reserved_stock(
        part=part,
        quantity=Decimal("4.00"),
        created_by=user,
        reason="Liberação de reserva.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RELEASE
    assert part.current_stock == Decimal("14.00")


@pytest.mark.django_db
def test_return_stock_increases_current_stock(part, user):
    """
    Test if stock return increases current stock.
    """
    movement = return_stock(
        part=part,
        quantity=Decimal("2.00"),
        created_by=user,
        reason="Devolução de peça.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RETURN
    assert part.current_stock == Decimal("12.00")


@pytest.mark.django_db
def test_adjust_stock_sets_exact_current_stock(part, user):
    """
    Test if stock adjustment sets exact current stock.
    """
    movement = adjust_stock(
        part=part,
        new_quantity=Decimal("25.00"),
        created_by=user,
        reason="Inventário físico.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.ADJUST
    assert part.current_stock == Decimal("25.00")


@pytest.mark.django_db
def test_service_rejects_zero_quantity(part, user):
    """
    Test if service rejects zero quantity.
    """
    with pytest.raises(ValidationError):
        create_stock_entry(
            part=part,
            quantity=Decimal("0.00"),
            created_by=user,
            reason="Quantidade inválida.",
        )


@pytest.mark.django_db
def test_service_rejects_negative_quantity(part, user):
    """
    Test if service rejects negative quantity.
    """
    with pytest.raises(ValidationError):
        create_stock_entry(
            part=part,
            quantity=Decimal("-1.00"),
            created_by=user,
            reason="Quantidade inválida.",
        )
