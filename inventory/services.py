from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import Part, ServiceOrderPart, StockMovement


def validate_positive_quantity(quantity):
    """
    Validate if quantity is strictly greater than zero.
    Used for standard movements (IN, OUT, LOSS, etc).
    """
    if quantity <= Decimal("0.00"):
        raise ValidationError({"quantity": "A quantidade deve ser maior que zero."})


def validate_non_negative_adjustment(quantity):
    """
    Validate if adjustment target quantity is not negative.
    """
    if quantity < Decimal("0.00"):
        raise ValidationError(
            {"quantity": "A quantidade final de estoque não pode ser negativa."}
        )


def validate_available_stock(part, quantity):
    """
    Validate if part has enough stock for removals.
    """
    if quantity > part.current_stock:
        raise ValidationError(
            {"quantity": f"Estoque insuficiente. Disponível: {part.current_stock}"}
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
    Core function to create stock movements and update part stock safely.
    """
    # 1. Type conversion
    try:
        quantity = Decimal(str(quantity))
    except (ValueError, TypeError) as err:
        raise ValidationError({"quantity": "Quantidade inválida."}) from err

    # 2. Basic Quantity Validation (Strictly positive for most, non-negative for ADJUST)
    if movement_type == StockMovement.MovementType.ADJUST:
        validate_non_negative_adjustment(quantity)
    else:
        validate_positive_quantity(quantity)

    # 3. Audit validation (Reason is mandatory)
    if not reason or len(reason.strip()) < 5:
        raise ValidationError(
            {
                "reason": "Uma justificativa detalhada (mínimo 5 caracteres) é obrigatória."
            }
        )

    unit_cost = part.cost_price if unit_cost is None else Decimal(str(unit_cost))
    unit_sale_price = (
        part.sale_price if unit_sale_price is None else Decimal(str(unit_sale_price))
    )

    with transaction.atomic():
        locked_part = Part.objects.select_for_update().get(pk=part.pk)
        old_stock = locked_part.current_stock

        if movement_type in [
            StockMovement.MovementType.OUT,
            StockMovement.MovementType.LOSS,
            StockMovement.MovementType.RESERVE,
        ]:
            validate_available_stock(part=locked_part, quantity=quantity)
            locked_part.current_stock -= quantity

        elif movement_type in [
            StockMovement.MovementType.IN,
            StockMovement.MovementType.RETURN,
            StockMovement.MovementType.RELEASE,
        ]:
            locked_part.current_stock += quantity

        elif movement_type == StockMovement.MovementType.ADJUST:
            locked_part.current_stock = quantity

        locked_part.save(update_fields=["current_stock", "updated_at"])

        movement = StockMovement.objects.create(
            part=locked_part,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            unit_sale_price=unit_sale_price,
            reason=f"[AUDIT] De {old_stock} para {locked_part.current_stock}: {reason}",
            service_order=service_order,
            created_by=created_by,
        )

    return movement


def create_stock_entry(
    *, part, quantity, created_by, reason, unit_cost=None, unit_sale_price=None
):
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


def create_stock_loss(*, part, quantity, created_by, reason):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.LOSS,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
    )


def reserve_stock(*, part, quantity, created_by, reason, service_order=None):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RESERVE,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def release_reserved_stock(*, part, quantity, created_by, reason, service_order=None):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RELEASE,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def return_stock(*, part, quantity, created_by, reason, service_order=None):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.RETURN,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def adjust_stock(*, part, new_quantity, created_by, reason):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.ADJUST,
        quantity=new_quantity,
        created_by=created_by,
        reason=reason,
    )


@transaction.atomic
def reserve_part_for_service_order(*, service_order, form, created_by):
    if service_order.status == "canceled":
        raise ValidationError("Não é possível adicionar peças a uma OS cancelada.")

    service_order_part = form.save(commit=False)
    service_order_part.service_order = service_order
    service_order_part.created_by = created_by
    service_order_part.status = ServiceOrderPart.Status.RESERVED

    reserve_stock(
        part=service_order_part.part,
        quantity=service_order_part.quantity,
        created_by=created_by,
        reason=f"Reserva automática para OS #{service_order.pk}.",
        service_order=service_order,
    )

    service_order_part.full_clean()
    service_order_part.save()

    return service_order_part


@transaction.atomic
def confirm_service_order_part_usage(*, service_order_part):
    if service_order_part.status != ServiceOrderPart.Status.RESERVED:
        raise ValidationError(
            "Somente peças reservadas podem ser confirmadas como usadas."
        )

    service_order_part.status = ServiceOrderPart.Status.USED
    service_order_part.save(update_fields=["status", "updated_at"])

    return service_order_part


@transaction.atomic
def cancel_reserved_service_order_part(*, service_order_part, changed_by):
    if service_order_part.status != ServiceOrderPart.Status.RESERVED:
        raise ValidationError("Somente peças reservadas podem ser canceladas.")

    release_reserved_stock(
        part=service_order_part.part,
        quantity=service_order_part.quantity,
        created_by=changed_by,
        reason=f"Cancelamento da reserva da OS #{service_order_part.service_order_id}.",
        service_order=service_order_part.service_order,
    )

    service_order_part.status = ServiceOrderPart.Status.CANCELED
    service_order_part.save(update_fields=["status", "updated_at"])

    return service_order_part


@transaction.atomic
def return_used_service_order_part(*, service_order_part, changed_by):
    locked_service_order_part = (
        ServiceOrderPart.objects.select_for_update()
        .select_related("part", "service_order")
        .get(pk=service_order_part.pk)
    )

    if locked_service_order_part.status != ServiceOrderPart.Status.USED:
        raise ValidationError("Somente peças usadas podem ser devolvidas ao estoque.")

    return_stock(
        part=locked_service_order_part.part,
        quantity=locked_service_order_part.quantity,
        created_by=changed_by,
        reason=f"Devolução da peça da OS #{locked_service_order_part.service_order_id}.",
        service_order=locked_service_order_part.service_order,
    )

    locked_service_order_part.status = ServiceOrderPart.Status.RETURNED
    locked_service_order_part.save(update_fields=["status", "updated_at"])

    return locked_service_order_part
