from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import ServiceOrderPart
from inventory.services import reserve_stock
from service_orders.models import ServiceOrder, ServiceOrderItem


def validate_order_can_receive_services(service_order):
    if service_order.status == ServiceOrder.Status.CANCELED:
        raise ValidationError("Não é possível adicionar serviços a uma OS cancelada.")

    if service_order.is_budget_approved:
        raise ValidationError(
            "Orçamento aprovado não permite adicionar serviços ao valor da OS."
        )


def validate_active_service(service):
    if not service.is_active:
        raise ValidationError("Não é possível usar um serviço inativo.")


def validate_active_combo(combo):
    if not combo.is_active:
        raise ValidationError("Não é possível usar um combo inativo.")


def validate_combo_has_items(combo):
    if not combo.items.exists():
        raise ValidationError("O combo precisa ter pelo menos um serviço ativo.")


def create_service_order_item_with_default_parts(
    *,
    service_order,
    service,
    quantity,
    unit_price,
    created_by,
    description_prefix="",
):
    service_order_item = ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description=f"{description_prefix}{service.code} - {service.name}",
        quantity=quantity,
        unit_price=unit_price,
    )

    default_parts = list(
        service.default_parts.select_related("part").filter(is_active=True)
    )

    for default_part in default_parts:
        total_part_quantity = default_part.quantity * quantity
        part_unit_price = default_part.effective_unit_price

        reserve_stock(
            part=default_part.part,
            quantity=total_part_quantity,
            created_by=created_by,
            reason=(
                f"Reserva automática da peça {default_part.part.internal_code} "
                f"ao adicionar o serviço {service.code} na OS {service_order.display_number}."
            ),
            service_order=service_order,
        )

        ServiceOrderPart.objects.create(
            service_order=service_order,
            service_order_item=service_order_item,
            part=default_part.part,
            quantity=total_part_quantity,
            unit_price=part_unit_price,
            discount=Decimal("0.00"),
            status=ServiceOrderPart.Status.RESERVED,
            created_by=created_by,
        )

    return service_order_item


@transaction.atomic
def add_catalog_service_to_order(
    *,
    service_order,
    service,
    quantity,
    unit_price=None,
    created_by,
):
    validate_order_can_receive_services(service_order)
    validate_active_service(service)

    quantity = Decimal(str(quantity))

    if quantity <= Decimal("0.00"):
        raise ValidationError("A quantidade deve ser maior que zero.")

    if unit_price in [None, ""]:
        unit_price = service.default_price
    else:
        unit_price = Decimal(str(unit_price))

    if unit_price < Decimal("0.00"):
        raise ValidationError("O preço unitário não pode ser negativo.")

    return create_service_order_item_with_default_parts(
        service_order=service_order,
        service=service,
        quantity=quantity,
        unit_price=unit_price,
        created_by=created_by,
    )


@transaction.atomic
def add_combo_to_order(*, service_order, combo, created_by):
    validate_order_can_receive_services(service_order)
    validate_active_combo(combo)
    validate_combo_has_items(combo)

    combo_items = list(combo.items.select_related("service").all())
    gross_total = sum(
        (item.quantity * item.unit_price for item in combo_items), Decimal("0.00")
    )

    if combo.discount_amount > gross_total:
        raise ValidationError("O desconto do combo não pode ser maior que o subtotal.")

    created_items = []
    remaining_discount = combo.discount_amount

    for index, combo_item in enumerate(combo_items):
        validate_active_service(combo_item.service)

        line_total = combo_item.quantity * combo_item.unit_price

        if gross_total > Decimal("0.00") and combo.discount_amount > Decimal("0.00"):
            if index == len(combo_items) - 1:
                line_discount = remaining_discount
            else:
                line_discount = (
                    line_total / gross_total * combo.discount_amount
                ).quantize(Decimal("0.01"))
                remaining_discount -= line_discount

            discounted_line_total = max(line_total - line_discount, Decimal("0.00"))
            unit_price = (discounted_line_total / combo_item.quantity).quantize(
                Decimal("0.01")
            )
        else:
            unit_price = combo_item.unit_price

        created_items.append(
            create_service_order_item_with_default_parts(
                service_order=service_order,
                service=combo_item.service,
                quantity=combo_item.quantity,
                unit_price=unit_price,
                created_by=created_by,
                description_prefix=f"Combo {combo.code} - {combo.name}: ",
            )
        )

    return created_items
