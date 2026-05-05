from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from service_orders.models import ServiceOrder, ServiceOrderItem
from workshop_services.models import ServiceCombo, WorkshopService


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


@transaction.atomic
def add_catalog_service_to_order(*, service_order, service, quantity, unit_price=None):
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

    return ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description=f"{service.code} - {service.name}",
        quantity=quantity,
        unit_price=unit_price,
    )


@transaction.atomic
def add_combo_to_order(*, service_order, combo):
    validate_order_can_receive_services(service_order)
    validate_active_combo(combo)
    validate_combo_has_items(combo)

    combo_items = list(combo.items.select_related("service").all())
    gross_total = sum((item.quantity * item.unit_price for item in combo_items), Decimal("0.00"))

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
                line_discount = (line_total / gross_total * combo.discount_amount).quantize(Decimal("0.01"))
                remaining_discount -= line_discount

            discounted_line_total = max(line_total - line_discount, Decimal("0.00"))
            unit_price = (discounted_line_total / combo_item.quantity).quantize(Decimal("0.01"))
        else:
            unit_price = combo_item.unit_price

        created_items.append(
            ServiceOrderItem.objects.create(
                service_order=service_order,
                item_type=ServiceOrderItem.ItemType.SERVICE,
                description=(
                    f"Combo {combo.code} - {combo.name}: "
                    f"{combo_item.service.code} - {combo_item.service.name}"
                ),
                quantity=combo_item.quantity,
                unit_price=unit_price,
            )
        )

    return created_items
