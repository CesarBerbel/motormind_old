from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from inventory.models import Part, StockMovement


@pytest.fixture
def user():
    """
    Create user for inventory tests.
    """
    User = get_user_model()

    return User.objects.create_user(
        email="inventory_user@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def part():
    """
    Create part for inventory tests.
    """
    return Part.objects.create(
        name="Pastilha de freio",
        internal_code="BRK-001",
        barcode="789000000001",
        brand="Bosch",
        category="Freio",
        unit="un",
        cost_price=Decimal("80.00"),
        sale_price=Decimal("150.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("3.00"),
        location="Prateleira A1",
    )


@pytest.mark.django_db
def test_part_str(part):
    """
    Test part string representation.
    """
    assert str(part) == "BRK-001 - Pastilha de freio"


@pytest.mark.django_db
def test_part_low_stock_returns_false_when_stock_is_above_minimum(part):
    """
    Test low stock property when stock is above minimum.
    """
    assert part.is_low_stock is False
    assert part.stock_status_label == "Estoque normal"


@pytest.mark.django_db
def test_part_low_stock_returns_true_when_stock_is_equal_to_minimum(part):
    """
    Test low stock property when stock is equal to minimum.
    """
    part.current_stock = Decimal("3.00")
    part.save()

    assert part.is_low_stock is True
    assert part.stock_status_label == "Estoque baixo"


@pytest.mark.django_db
def test_stock_movement_str(part, user):
    """
    Test stock movement string representation.
    """
    movement = StockMovement.objects.create(
        part=part,
        movement_type=StockMovement.MovementType.IN,
        quantity=Decimal("5.00"),
        unit_cost=Decimal("80.00"),
        unit_sale_price=Decimal("150.00"),
        reason="Entrada inicial de estoque.",
        created_by=user,
    )

    assert str(movement) == "Entrada - Pastilha de freio"


@pytest.mark.django_db
def test_stock_movement_requires_positive_quantity(part, user):
    """
    Test if stock movement quantity must be positive.
    """
    movement = StockMovement(
        part=part,
        movement_type=StockMovement.MovementType.IN,
        quantity=Decimal("0.00"),
        unit_cost=Decimal("80.00"),
        unit_sale_price=Decimal("150.00"),
        reason="Movimentação inválida.",
        created_by=user,
    )

    with pytest.raises(ValidationError):
        movement.full_clean()


@pytest.mark.django_db
def test_stock_movement_blocks_out_when_stock_is_insufficient(part, user):
    """
    Test if stock movement blocks output when stock is insufficient.
    """
    movement = StockMovement(
        part=part,
        movement_type=StockMovement.MovementType.OUT,
        quantity=Decimal("20.00"),
        unit_cost=Decimal("80.00"),
        unit_sale_price=Decimal("150.00"),
        reason="Saída maior que o estoque.",
        created_by=user,
    )

    with pytest.raises(ValidationError):
        movement.full_clean()


@pytest.mark.django_db
def test_stock_movement_allows_out_when_stock_is_sufficient(part, user):
    """
    Test if stock movement allows output when stock is sufficient.
    """
    movement = StockMovement(
        part=part,
        movement_type=StockMovement.MovementType.OUT,
        quantity=Decimal("2.00"),
        unit_cost=Decimal("80.00"),
        unit_sale_price=Decimal("150.00"),
        reason="Saída válida.",
        created_by=user,
    )

    movement.full_clean()

    assert movement.quantity == Decimal("2.00")


@pytest.mark.django_db
def test_stock_movement_allows_input_without_stock_validation(part, user):
    """
    Test if stock input does not require previous available stock.
    """
    part.current_stock = Decimal("0.00")
    part.save()

    movement = StockMovement(
        part=part,
        movement_type=StockMovement.MovementType.IN,
        quantity=Decimal("15.00"),
        unit_cost=Decimal("80.00"),
        unit_sale_price=Decimal("150.00"),
        reason="Entrada com estoque anterior zerado.",
        created_by=user,
    )

    movement.full_clean()

    assert movement.quantity == Decimal("15.00")
