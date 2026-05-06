from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import AuditLog
from auditoria.services import log_event
from inventory.models import Part, PurchaseOrder, ServiceOrderPart, StockMovement

DECIMAL_2 = Decimal("0.01")


def quantize_2(value):
    if value in [None, ""]:
        return Decimal("0.00")

    try:
        return Decimal(str(value)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError("Valor decimal inválido.") from error


def to_decimal(value, field_name="quantidade"):
    try:
        return quantize_2(value)
    except ValidationError as error:
        raise ValidationError({field_name: "Valor inválido."}) from error


def validate_reason(reason):
    if not reason or len(reason.strip()) < 5:
        raise ValidationError(
            {"reason": "A justificativa deve conter pelo menos 5 caracteres."}
        )


def validate_positive_quantity(quantity):
    if quantity <= Decimal("0.00"):
        raise ValidationError({"quantity": "A quantidade deve ser maior que zero."})


def validate_non_negative_quantity(quantity):
    if quantity < Decimal("0.00"):
        raise ValidationError({"quantity": "A quantidade não pode ser negativa."})


def validate_available_stock(part, quantity):
    if quantity > part.current_stock:
        raise ValidationError(
            {"quantity": f"Estoque insuficiente. Disponível: {part.current_stock}."}
        )


def get_reservable_quantity(part, requested_quantity):
    available = quantize_2(part.current_stock)
    requested_quantity = quantize_2(requested_quantity)

    if available <= Decimal("0.00"):
        return Decimal("0.00")

    return min(available, requested_quantity)


def create_purchase_order_for_shortage(
    *,
    part,
    service_order,
    service_order_part,
    requested_quantity,
    reserved_quantity,
    created_by,
    reason,
):
    shortage_quantity = quantize_2(requested_quantity - reserved_quantity)

    if shortage_quantity <= Decimal("0.00"):
        return None

    purchase_order = PurchaseOrder.objects.create(
        part=part,
        service_order=service_order,
        service_order_part=service_order_part,
        requested_quantity=shortage_quantity,
        status=PurchaseOrder.Status.OPEN,
        reason=reason,
        created_by=created_by,
    )

    log_event(
        action=AuditLog.Action.STOCK_MOVEMENT,
        user=created_by,
        obj=purchase_order,
        old_data={},
        new_data={
            "part_id": part.pk,
            "service_order_id": service_order.pk,
            "service_order_part_id": (
                service_order_part.pk if service_order_part else None
            ),
            "requested_quantity": str(shortage_quantity),
        },
        metadata={"movement_type": "purchase_order_opened"},
    )

    return purchase_order


def validate_active_part(part):
    if not part.is_active:
        raise ValidationError("Não é possível movimentar uma peça inativa.")


def validate_service_order_can_receive_part(service_order):
    if service_order.status == "canceled":
        raise ValidationError("Não é possível adicionar peças a uma OS cancelada.")


def get_default_unit_cost(part, unit_cost):
    if unit_cost is None:
        return quantize_2(part.cost_price)

    return to_decimal(unit_cost, field_name="unit_cost")


def get_default_unit_sale_price(part, unit_sale_price):
    if unit_sale_price is None:
        return quantize_2(part.sale_price)

    return to_decimal(unit_sale_price, field_name="unit_sale_price")


def build_audit_reason(old_stock, new_stock, reason):
    return f"[AUDIT] De {old_stock} para {new_stock}: {reason}"


@transaction.atomic
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
    quantity = to_decimal(quantity)
    validate_reason(reason)

    if movement_type == StockMovement.MovementType.ADJUST:
        validate_non_negative_quantity(quantity)
    else:
        validate_positive_quantity(quantity)

    locked_part = Part.objects.select_for_update().get(pk=part.pk)
    validate_active_part(locked_part)

    old_stock = quantize_2(locked_part.current_stock)

    if movement_type in [
        StockMovement.MovementType.OUT,
        StockMovement.MovementType.LOSS,
        StockMovement.MovementType.RESERVE,
    ]:
        validate_available_stock(locked_part, quantity)
        locked_part.current_stock = quantize_2(locked_part.current_stock - quantity)

    elif movement_type in [
        StockMovement.MovementType.IN,
        StockMovement.MovementType.RETURN,
        StockMovement.MovementType.RELEASE,
    ]:
        locked_part.current_stock = quantize_2(locked_part.current_stock + quantity)

    elif movement_type == StockMovement.MovementType.ADJUST:
        locked_part.current_stock = quantize_2(quantity)

    else:
        raise ValidationError({"movement_type": "Tipo de movimentação inválido."})

    locked_part.save(update_fields=["current_stock", "updated_at"])

    movement = StockMovement.objects.create(
        part=locked_part,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=get_default_unit_cost(locked_part, unit_cost),
        unit_sale_price=get_default_unit_sale_price(locked_part, unit_sale_price),
        reason=build_audit_reason(old_stock, locked_part.current_stock, reason),
        service_order=service_order,
        created_by=created_by,
    )

    log_event(
        action=AuditLog.Action.STOCK_MOVEMENT,
        user=created_by,
        obj=movement,
        old_data={"part_id": locked_part.pk, "stock": str(old_stock)},
        new_data={"part_id": locked_part.pk, "stock": str(locked_part.current_stock)},
        metadata={"movement_type": movement_type, "quantity": str(quantity)},
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
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.IN,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        unit_cost=unit_cost,
        unit_sale_price=unit_sale_price,
    )


def create_stock_output(*, part, quantity, created_by, reason, service_order=None):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.OUT,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
    )


def create_stock_loss(*, part, quantity, created_by, reason, service_order=None):
    return create_stock_movement(
        part=part,
        movement_type=StockMovement.MovementType.LOSS,
        quantity=quantity,
        created_by=created_by,
        reason=reason,
        service_order=service_order,
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
    validate_service_order_can_receive_part(service_order)

    service_order_part = form.save(commit=False)
    service_order_part.service_order = service_order
    service_order_part.created_by = created_by
    service_order_part.quantity = quantize_2(service_order_part.quantity)
    service_order_part.unit_price = quantize_2(service_order_part.unit_price)
    service_order_part.discount = quantize_2(service_order_part.discount)

    locked_part = Part.objects.select_for_update().get(pk=service_order_part.part_id)
    service_order_part.part = locked_part
    reservable_quantity = get_reservable_quantity(
        locked_part, service_order_part.quantity
    )
    service_order_part.reserved_quantity = reservable_quantity
    service_order_part.status = (
        ServiceOrderPart.Status.RESERVED
        if reservable_quantity >= service_order_part.quantity
        else ServiceOrderPart.Status.WAITING_PURCHASE
    )

    service_order_part.full_clean()

    if reservable_quantity > Decimal("0.00"):
        reserve_stock(
            part=locked_part,
            quantity=reservable_quantity,
            created_by=created_by,
            reason=f"Reserva automática para OS #{service_order.pk}.",
            service_order=service_order,
        )

    service_order_part.save()

    create_purchase_order_for_shortage(
        part=locked_part,
        service_order=service_order,
        service_order_part=service_order_part,
        requested_quantity=service_order_part.quantity,
        reserved_quantity=reservable_quantity,
        created_by=created_by,
        reason=(
            f"Pedido de compra aberto automaticamente para atender a OS "
            f"#{service_order.pk}. Quantidade solicitada: "
            f"{service_order_part.quantity}; reservada em estoque: "
            f"{reservable_quantity}."
        ),
    )

    return service_order_part


@transaction.atomic
def confirm_service_order_part_usage(*, service_order_part):
    locked_part_link = (
        ServiceOrderPart.objects.select_for_update()
        .select_related("part", "service_order")
        .get(pk=service_order_part.pk)
    )

    if locked_part_link.status not in [
        ServiceOrderPart.Status.RESERVED,
        ServiceOrderPart.Status.WAITING_PURCHASE,
    ]:
        raise ValidationError(
            "Apenas peças reservadas ou aguardando compra podem ser confirmadas como usadas."
        )

    if locked_part_link.reserved_quantity < locked_part_link.quantity:
        raise ValidationError(
            "A peça ainda possui quantidade pendente de compra/entrada no estoque."
        )

    locked_part_link.status = ServiceOrderPart.Status.USED
    locked_part_link.save(update_fields=["status", "updated_at"])

    return locked_part_link


@transaction.atomic
def cancel_service_order_part_reservation(*, service_order_part, created_by):
    locked_part_link = (
        ServiceOrderPart.objects.select_for_update()
        .select_related("part", "service_order")
        .get(pk=service_order_part.pk)
    )

    if locked_part_link.status not in [
        ServiceOrderPart.Status.RESERVED,
        ServiceOrderPart.Status.WAITING_PURCHASE,
    ]:
        raise ValidationError("Apenas reservas podem ser canceladas.")

    if locked_part_link.reserved_quantity > Decimal("0.00"):
        release_reserved_stock(
            part=locked_part_link.part,
            quantity=locked_part_link.reserved_quantity,
            created_by=created_by,
            reason=f"Cancelamento de reserva da OS #{locked_part_link.service_order.pk}.",
            service_order=locked_part_link.service_order,
        )

    PurchaseOrder.objects.filter(
        service_order_part=locked_part_link,
        status=PurchaseOrder.Status.OPEN,
    ).update(status=PurchaseOrder.Status.CANCELED)

    locked_part_link.status = ServiceOrderPart.Status.CANCELED
    locked_part_link.save(update_fields=["status", "updated_at"])

    return locked_part_link


@transaction.atomic
def return_service_order_part(*, service_order_part, created_by):
    locked_part_link = (
        ServiceOrderPart.objects.select_for_update()
        .select_related("part", "service_order")
        .get(pk=service_order_part.pk)
    )

    if locked_part_link.status != ServiceOrderPart.Status.USED:
        raise ValidationError("Apenas peças usadas podem ser devolvidas.")

    return_stock(
        part=locked_part_link.part,
        quantity=locked_part_link.quantity,
        created_by=created_by,
        reason=f"Devolução de peça usada na OS #{locked_part_link.service_order.pk}.",
        service_order=locked_part_link.service_order,
    )

    locked_part_link.status = ServiceOrderPart.Status.RETURNED
    locked_part_link.save(update_fields=["status", "updated_at"])

    return locked_part_link


@transaction.atomic
def reserve_catalog_part_for_service_order_item(
    *,
    service_order,
    service_order_item,
    part,
    quantity,
    unit_price,
    created_by,
    reason,
):
    """
    Reserva uma peça automaticamente quando um serviço do catálogo é adicionado à OS.
    """
    validate_service_order_can_receive_part(service_order)

    if service_order_item.service_order_id != service_order.pk:
        raise ValidationError(
            "O serviço informado não pertence à mesma ordem de serviço da peça."
        )

    quantity = quantize_2(quantity)
    unit_price = quantize_2(unit_price)
    validate_positive_quantity(quantity)

    locked_part = Part.objects.select_for_update().get(pk=part.pk)
    reservable_quantity = get_reservable_quantity(locked_part, quantity)

    service_order_part = ServiceOrderPart(
        service_order=service_order,
        service_order_item=service_order_item,
        part=locked_part,
        quantity=quantity,
        reserved_quantity=reservable_quantity,
        unit_price=unit_price,
        discount=Decimal("0.00"),
        status=(
            ServiceOrderPart.Status.RESERVED
            if reservable_quantity >= quantity
            else ServiceOrderPart.Status.WAITING_PURCHASE
        ),
        created_by=created_by,
    )
    service_order_part.full_clean()

    if reservable_quantity > Decimal("0.00"):
        reserve_stock(
            part=locked_part,
            quantity=reservable_quantity,
            created_by=created_by,
            reason=reason,
            service_order=service_order,
        )

    service_order_part.save()

    create_purchase_order_for_shortage(
        part=locked_part,
        service_order=service_order,
        service_order_part=service_order_part,
        requested_quantity=quantity,
        reserved_quantity=reservable_quantity,
        created_by=created_by,
        reason=(
            f"Pedido de compra aberto automaticamente para peça associada "
            f"ao serviço da OS #{service_order.pk}. Quantidade solicitada: "
            f"{quantity}; reservada em estoque: {reservable_quantity}."
        ),
    )

    return service_order_part


# Aliases de compatibilidade com as views existentes.
# Mantêm os nomes antigos usados em inventory/views/service_order_part_views.py.


def cancel_reserved_service_order_part(
    *,
    service_order_part,
    changed_by=None,
    created_by=None,
):
    user = changed_by or created_by

    return cancel_service_order_part_reservation(
        service_order_part=service_order_part,
        created_by=user,
    )


def confirm_reserved_service_order_part(
    *,
    service_order_part,
    changed_by=None,
    created_by=None,
):
    return confirm_service_order_part_usage(
        service_order_part=service_order_part,
    )


def return_used_service_order_part(
    *,
    service_order_part,
    changed_by=None,
    created_by=None,
):
    user = changed_by or created_by

    return return_service_order_part(
        service_order_part=service_order_part,
        created_by=user,
    )
