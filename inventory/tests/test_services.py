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
    # Create a standard user for testing purposes
    return User.objects.create_user(
        email="inventory_service_user@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def part():
    """
    Create part for inventory service tests.
    """
    # Create an initial part with 10 units in stock[cite: 22]
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
    # Act: Create an entry movement[cite: 25, 34]
    movement = create_stock_entry(
        part=part,
        quantity=Decimal("5.00"),
        created_by=user,
        reason="Entrada de compra via teste.",  # Reason must be >= 5 chars
    )

    part.refresh_from_db()

    # Assert: Check type and new stock level[cite: 25]
    assert movement.movement_type == StockMovement.MovementType.IN
    assert part.current_stock == Decimal("15.00")


@pytest.mark.django_db
def test_create_stock_output_decreases_current_stock(part, user):
    """
    Test if stock output decreases current stock.
    """
    # Act: Create an output movement[cite: 25, 34]
    movement = create_stock_output(
        part=part,
        quantity=Decimal("3.00"),
        created_by=user,
        reason="Saída manual via teste.",
    )

    part.refresh_from_db()

    # Assert: Check type and new stock level[cite: 25]
    assert movement.movement_type == StockMovement.MovementType.OUT
    assert part.current_stock == Decimal("7.00")


@pytest.mark.django_db
def test_create_stock_output_blocks_negative_stock(part, user):
    """
    Test if stock output blocks insufficient stock.
    """
    # Assert: Should raise ValidationError due to insufficient stock[cite: 25, 32]
    with pytest.raises(ValidationError):
        create_stock_output(
            part=part,
            quantity=Decimal("20.00"),
            created_by=user,
            reason="Saída maior que o estoque disponível.",
        )

    part.refresh_from_db()
    # Stock should remain unchanged[cite: 25]
    assert part.current_stock == Decimal("10.00")


@pytest.mark.django_db
def test_create_stock_loss_decreases_current_stock(part, user):
    """
    Test if stock loss decreases current stock.
    """
    # Act: Create a loss movement[cite: 25]
    movement = create_stock_loss(
        part=part,
        quantity=Decimal("2.00"),
        created_by=user,
        reason="Peça danificada no manuseio.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.LOSS
    assert part.current_stock == Decimal("8.00")


@pytest.mark.django_db
def test_reserve_stock_decreases_current_stock(part, user):
    """
    Test if stock reservation decreases available stock.
    """
    # Act: Create a reservation[cite: 25]
    movement = reserve_stock(
        part=part,
        quantity=Decimal("4.00"),
        created_by=user,
        reason="Reserva para ordem de serviço teste.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RESERVE
    assert part.current_stock == Decimal("6.00")


@pytest.mark.django_db
def test_release_reserved_stock_increases_current_stock(part, user):
    """
    Test if releasing reserved stock increases current stock.
    """
    # Act: Create a release movement[cite: 25]
    movement = release_reserved_stock(
        part=part,
        quantity=Decimal("4.00"),
        created_by=user,
        reason="Liberação de reserva não utilizada.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RELEASE
    assert part.current_stock == Decimal("14.00")


@pytest.mark.django_db
def test_return_stock_increases_current_stock(part, user):
    """
    Test if stock return increases current stock.
    """
    # Act: Create a return movement[cite: 25]
    movement = return_stock(
        part=part,
        quantity=Decimal("2.00"),
        created_by=user,
        reason="Devolução de peça pelo cliente.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.RETURN
    assert part.current_stock == Decimal("12.00")


@pytest.mark.django_db
def test_adjust_stock_sets_exact_current_stock(part, user):
    """
    Test if stock adjustment sets exact current stock.
    """
    # Act: Set stock directly to 25[cite: 25]
    movement = adjust_stock(
        part=part,
        new_quantity=Decimal("25.00"),
        created_by=user,
        reason="Ajuste via inventário físico anual.",
    )

    part.refresh_from_db()

    assert movement.movement_type == StockMovement.MovementType.ADJUST
    assert part.current_stock == Decimal("25.00")


@pytest.mark.django_db
def test_service_rejects_zero_quantity(part, user):
    """
    Test if service rejects zero quantity for standard movements.
    """
    # Assert: Standard movements must have quantity > 0[cite: 25, 34]
    with pytest.raises(ValidationError) as excinfo:
        create_stock_entry(
            part=part,
            quantity=Decimal("0.00"),
            created_by=user,
            reason="Justificativa válida de teste.",
        )

    # Check if the error message is related to quantity[cite: 32, 34]
    assert "quantity" in excinfo.value.message_dict


@pytest.mark.django_db
def test_service_rejects_negative_quantity(part, user):
    """
    Test if service rejects negative quantity.
    """
    # Assert: Should raise ValidationError for negative values[cite: 25]
    with pytest.raises(ValidationError) as excinfo:
        create_stock_entry(
            part=part,
            quantity=Decimal("-1.00"),
            created_by=user,
            reason="Justificativa válida de teste.",
        )

    assert "quantity" in excinfo.value.message_dict


@pytest.mark.django_db
def test_service_rejects_short_reason(part, user):
    """
    Test if service rejects a reason that is too short for audit.
    """
    # New test case to ensure audit rule is working
    with pytest.raises(ValidationError) as excinfo:
        create_stock_entry(
            part=part,
            quantity=Decimal("1.00"),
            created_by=user,
            reason="abc",  # Too short
        )

    assert "reason" in excinfo.value.message_dict
