from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

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


@transaction.atomic
def add_catalog_service_to_order(
    *,
    service_order,
    catalog_service=None,
    service=None,
    quantity=Decimal("1.00"),
    discount=Decimal("0.00"),
    created_by=None,
):
    """
    Add a catalog service to a service order using the catalog default price.

    Accepts both catalog_service and service for backward compatibility with
    older tests/views.
    """
    catalog_service = catalog_service or service

    if catalog_service is None:
        raise ValueError("Informe o serviço do catálogo.")

    quantity = quantity or Decimal("1.00")
    discount = discount or Decimal("0.00")

    if quantity <= Decimal("0.00"):
        raise ValueError("A quantidade deve ser maior que zero.")

    if discount < Decimal("0.00"):
        raise ValueError("O desconto não pode ser negativo.")

    unit_price = catalog_service.default_price
    subtotal = quantity * unit_price

    if discount > subtotal:
        raise ValueError("O desconto não pode ser maior que o subtotal.")

    service_code = getattr(catalog_service, "internal_code", None) or getattr(
        catalog_service,
        "code",
        "",
    )

    service_name = getattr(catalog_service, "name", "")

    if service_code:
        description = f"{service_code} - {service_name}"
    else:
        description = service_name

    item_data = {
        "service_order": service_order,
        "item_type": "service",
        "description": description,
        "quantity": quantity,
        "unit_price": unit_price,
    }

    if any(field.name == "discount" for field in ServiceOrderItem._meta.fields):
        item_data["discount"] = discount

    if any(field.name == "created_by" for field in ServiceOrderItem._meta.fields):
        item_data["created_by"] = created_by

    return ServiceOrderItem.objects.create(**item_data)


@transaction.atomic
def add_combo_to_order(*, service_order, combo):
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
