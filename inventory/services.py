from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import Part, StockMovement


def validate_positive_quantity(quantity):
    """
    Validate if quantity is greater than zero.
    """
    if quantity <= Decimal("0.00"):
        raise ValidationError(
            {
                "quantity": "A quantidade deve ser maior que zero.",
            }
        )


def validate_available_stock(part, quantity):
    """
    Validate if part has enough stock.
    """
    if quantity > part.current_stock:
        raise ValidationError(
            {
                "quantity": "Estoque insuficiente para esta movimentação.",
            }
        )


def create_stock_movement(
    *,
    part,
    movement_type,
    quantity,
    created_by,
    reason,
    unit_cost=None,
    unit_sale_price=None,
    service_order=None,
):
    """
    Create stock movement and update part stock safely.
    """
    quantity = Decimal(str(quantity))

    validate_positive_quantity(quantity)

    unit_cost = part.cost_price if unit_cost is None else Decimal(str(unit_cost))
    unit_sale_price = (
        part.sale_price if unit_sale_price is None else Decimal(str(unit_sale_price))
    )

    with transaction.atomic():
        locked_part = Part.objects.select_for_update().get(pk=part.pk)

        if movement_type in [
            StockMovement.MovementType.OUT,
            StockMovement.MovementType.LOSS,
            StockMovement.MovementType.RESERVE,
        ]:
            validate_available_stock(
                part=locked_part,
                quantity=quantity,
            )

            locked_part.current_stock -= quantity

        elif movement_type in [
            StockMovement.MovementType.IN,
            StockMovement.MovementType.RETURN,
            StockMovement.MovementType.RELEASE,
        ]:
            locked_part.current_stock += quantity

        elif movement_type == StockMovement.MovementType.ADJUST:
            locked_part.current_stock = quantity

        locked_part.save(
            update_fields=[
                "current_stock",
                "updated_at",
            ]
        )

        movement = StockMovement.objects.create(
            part=locked_part,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            unit_sale_price=unit_sale_price,
            reason=reason,
            service_order=service_order,
            created_by=created_by,
        )

    return movement


def create_stock_entry(
    *,
    part,
    quantity,
    created_by,
    reason,
    unit_cost=None,
    unit_sale_price=None,
):
    """
    Create stock input movement.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.IN,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        unit_cost=unit_cost,
        unit_sale_price=unit_sale_price,
    )


def create_stock_output(
    *,
    part,
    quantity,
    created_by,
    reason,
    unit_cost=None,
    unit_sale_price=None,
    service_order=None,
):
    """
    Create stock output movement.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.OUT,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        unit_cost=unit_cost,
        unit_sale_price=unit_sale_price,
        service_order=service_order,
    )


def create_stock_loss(
    *,
    part,
    quantity,
    created_by,
    reason,
):
    """
    Create stock loss movement.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.LOSS,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
    )


def reserve_stock(
    *,
    part,
    quantity,
    created_by,
    reason,
    service_order=None,
):
    """
    Reserve stock for a service order.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RESERVE,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def release_reserved_stock(
    *,
    part,
    quantity,
    created_by,
    reason,
    service_order=None,
):
    """
    Release reserved stock back to inventory.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RELEASE,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def return_stock(
    *,
    part,
    quantity,
    created_by,
    reason,
    service_order=None,
):
    """
    Return stock to inventory.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RETURN,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def adjust_stock(
    *,
    part,
    new_quantity,
    created_by,
    reason,
):
    """
    Adjust stock to an exact quantity.
    """
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.ADJUST,
        quantity=new_quantity,
        created_by=created_by,
        reason=reason,
    )
