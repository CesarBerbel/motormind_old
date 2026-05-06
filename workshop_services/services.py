from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from core.form_fields import normalize_money_value, normalize_quantity_value
from inventory.services import reserve_catalog_part_for_service_order_item
from service_orders.models import ServiceOrder, ServiceOrderItem
from workshop_services.models import (
    ServiceCombo,
    WorkshopCatalogAuditLog,
    WorkshopService,
    WorkshopServiceVersion,
)

DECIMAL_2 = Decimal("0.01")


def normalize_quantity(value):
    if value in [None, ""]:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def normalize_unit_price(value):
    value = normalize_money_value(value, default=Decimal("0.00"))
    return value if value is not None else Decimal("0.00")


def money(value):
    if value in [None, ""]:
        value = Decimal("0.00")

    return Decimal(str(value)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def normalize_service_quantity(value):
    return normalize_quantity_value(value, default=Decimal("0.00"))


def normalize_service_money(value):
    return normalize_money_value(value, default=Decimal("0.00"))


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


def service_snapshot(service):
    return {
        "id": service.pk,
        "code": service.code,
        "name": service.name,
        "category": str(service.category) if service.category_id else "",
        "description": service.description or "",
        "default_price": str(normalize_service_money(service.default_price)),
        "estimated_minutes": service.estimated_minutes,
        "current_version": service.current_version,
        "default_parts": [
            {
                "id": item.pk,
                "part_id": item.part_id,
                "part": str(item.part),
                "quantity": str(normalize_service_quantity(item.quantity)),
                "unit_price": str(normalize_service_money(item.effective_unit_price)),
                "is_active": item.is_active,
            }
            for item in service.default_parts.select_related("part").order_by(
                "created_at"
            )
        ],
    }


def combo_snapshot(combo):
    return {
        "id": combo.pk,
        "code": combo.code,
        "name": combo.name,
        "description": combo.description or "",
        "discount_amount": str(normalize_service_money(combo.discount_amount)),
        "is_active": combo.is_active,
        "items": [
            {
                "id": item.pk,
                "service_id": item.service_id,
                "service": str(item.service),
                "quantity": str(normalize_service_quantity(item.quantity)),
                "unit_price": str(normalize_service_money(item.unit_price)),
            }
            for item in combo.items.select_related("service").order_by("created_at")
        ],
    }


def create_service_version(service, *, created_by=None):
    next_version = service.versions.count() + 1
    service.current_version = next_version
    service.save(update_fields=["current_version", "updated_at"])

    version = WorkshopServiceVersion.objects.create(
        service=service,
        version_number=next_version,
        code_snapshot=service.code,
        name_snapshot=service.name,
        category_snapshot=str(service.category) if service.category_id else "",
        description_snapshot=service.description or "",
        default_price_snapshot=normalize_service_money(service.default_price),
        estimated_minutes_snapshot=service.estimated_minutes,
        parts_snapshot=service_snapshot(service)["default_parts"],
        created_by=(
            created_by if getattr(created_by, "is_authenticated", False) else None
        ),
    )

    return version


def log_catalog_change(
    *,
    action,
    user=None,
    service=None,
    combo=None,
    category=None,
    old_data=None,
    new_data=None,
):
    return WorkshopCatalogAuditLog.objects.create(
        action=action,
        service=service,
        combo=combo,
        category=category,
        changed_by=user if getattr(user, "is_authenticated", False) else None,
        old_data=old_data or {},
        new_data=new_data or {},
    )


@transaction.atomic
def save_category_with_audit(*, form, user=None, instance=None):
    old_data = {}

    if instance and instance.pk:
        old_data = {
            "name": instance.name,
            "parent_id": instance.parent_id,
            "is_active": instance.is_active,
        }

    category = form.save()

    action = (
        WorkshopCatalogAuditLog.Action.CATEGORY_UPDATED
        if old_data
        else WorkshopCatalogAuditLog.Action.CATEGORY_CREATED
    )

    log_catalog_change(
        action=action,
        user=user,
        category=category,
        old_data=old_data,
        new_data={
            "name": category.name,
            "parent_id": category.parent_id,
            "is_active": category.is_active,
        },
    )

    return category


@transaction.atomic
def save_service_with_parts_and_audit(*, form, formset, user=None, instance=None):
    old_data = service_snapshot(instance) if instance and instance.pk else {}

    service = form.save()
    formset.instance = service
    formset.save()
    service.refresh_from_db()

    create_service_version(service, created_by=user)

    new_data = service_snapshot(service)

    action = (
        WorkshopCatalogAuditLog.Action.SERVICE_UPDATED
        if old_data
        else WorkshopCatalogAuditLog.Action.SERVICE_CREATED
    )

    log_catalog_change(
        action=action,
        user=user,
        service=service,
        old_data=old_data,
        new_data=new_data,
    )

    log_catalog_change(
        action=WorkshopCatalogAuditLog.Action.SERVICE_PARTS_UPDATED,
        user=user,
        service=service,
        old_data={"default_parts": old_data.get("default_parts", [])},
        new_data={"default_parts": new_data.get("default_parts", [])},
    )

    return service


@transaction.atomic
def save_combo_with_items_and_audit(*, form, formset, user=None, instance=None):
    old_data = combo_snapshot(instance) if instance and instance.pk else {}

    combo = form.save()

    if hasattr(formset, "instance"):
        formset.instance = combo
        formset.save()
    else:
        for obj in formset.save(commit=False):
            obj.combo = combo
            obj.quantity = normalize_service_quantity(obj.quantity)
            obj.unit_price = normalize_service_money(obj.unit_price)
            obj.save()

        for obj in getattr(formset, "deleted_objects", []):
            obj.delete()

        formset.save_m2m()

    combo.refresh_from_db()

    new_data = combo_snapshot(combo)

    action = (
        WorkshopCatalogAuditLog.Action.COMBO_UPDATED
        if old_data
        else WorkshopCatalogAuditLog.Action.COMBO_CREATED
    )

    log_catalog_change(
        action=action,
        user=user,
        combo=combo,
        old_data=old_data,
        new_data=new_data,
    )

    log_catalog_change(
        action=WorkshopCatalogAuditLog.Action.COMBO_ITEMS_UPDATED,
        user=user,
        combo=combo,
        old_data={"items": old_data.get("items", [])},
        new_data={"items": new_data.get("items", [])},
    )

    return combo


def _create_order_service_item(
    *,
    service_order,
    service,
    quantity,
    unit_price,
    prefix="",
):
    description = f"{prefix}{service.code} - {service.name}"

    if service.current_version:
        description = f"{description} (v{service.current_version})"

    return ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description=description,
        quantity=normalize_service_quantity(quantity),
        unit_price=normalize_service_money(unit_price),
    )


def _copy_default_parts_to_order_service(
    *,
    service_order,
    service_order_item,
    service,
    service_quantity,
    created_by,
):
    parts = []

    service_quantity = normalize_service_quantity(service_quantity)

    for default_part in service.default_parts.select_related("part").all():
        part_quantity = normalize_service_quantity(
            default_part.quantity * service_quantity
        )

        if part_quantity <= Decimal("0.00"):
            continue

        unit_price = (
            default_part.unit_price
            if default_part.unit_price is not None
            else default_part.part.sale_price
        )
        unit_price = normalize_service_money(unit_price)

        part = reserve_catalog_part_for_service_order_item(
            service_order=service_order,
            service_order_item=service_order_item,
            part=default_part.part,
            quantity=part_quantity,
            unit_price=unit_price,
            created_by=created_by,
            reason=(
                f"Reserva automática da peça {default_part.part.name} "
                f"pelo serviço {service.name} na OS #{service_order.pk}."
            ),
        )

        parts.append(part)

    return parts


def _get_combo_lines(combo, combo_quantity):
    lines = []

    for combo_item in combo.items.select_related("service").all():
        service = combo_item.service
        validate_active_service(service)

        service_quantity = normalize_service_quantity(
            combo_item.quantity * combo_quantity
        )

        if service_quantity <= Decimal("0.00"):
            continue

        unit_price = (
            combo_item.unit_price
            if combo_item.unit_price is not None
            else service.default_price
        )
        unit_price = normalize_service_money(unit_price)

        gross_total = normalize_service_money(service_quantity * unit_price)

        lines.append(
            {
                "service": service,
                "quantity": service_quantity,
                "unit_price": unit_price,
                "gross_total": gross_total,
            }
        )

    return lines


def _apply_combo_discount_to_lines(lines, discount_amount):
    """
    Aplica o desconto do combo rateando o desconto nos próprios serviços.

    Assim:
    - não cria item extra de desconto;
    - a OS mostra apenas os serviços reais;
    - o total financeiro fica correto;
    - o teste funcional service_order.items.count() == quantidade de serviços continua coerente.
    """
    if not lines:
        return []

    discount_amount = normalize_service_money(discount_amount)

    if discount_amount <= Decimal("0.00"):
        return [
            {
                **line,
                "final_unit_price": line["unit_price"],
            }
            for line in lines
        ]

    gross_total = normalize_service_money(
        sum((line["gross_total"] for line in lines), Decimal("0.00"))
    )

    if gross_total <= Decimal("0.00"):
        return [
            {
                **line,
                "final_unit_price": Decimal("0.00"),
            }
            for line in lines
        ]

    discount_amount = min(discount_amount, gross_total)

    discounted_lines = []
    allocated_discount = Decimal("0.00")

    for index, line in enumerate(lines):
        is_last = index == len(lines) - 1

        if is_last:
            line_discount = normalize_service_money(
                discount_amount - allocated_discount
            )
        else:
            ratio = line["gross_total"] / gross_total
            line_discount = normalize_service_money(discount_amount * ratio)
            allocated_discount = normalize_service_money(
                allocated_discount + line_discount
            )

        final_line_total = normalize_service_money(line["gross_total"] - line_discount)

        if final_line_total < Decimal("0.00"):
            final_line_total = Decimal("0.00")

        final_unit_price = normalize_service_money(final_line_total / line["quantity"])

        discounted_lines.append(
            {
                **line,
                "discount": line_discount,
                "final_line_total": final_line_total,
                "final_unit_price": final_unit_price,
            }
        )

    return discounted_lines


@transaction.atomic
def add_catalog_service_to_order(
    *,
    service_order,
    service,
    quantity,
    unit_price=None,
    created_by=None,
):
    validate_order_can_receive_services(service_order)
    validate_active_service(service)

    service = (
        WorkshopService.objects.select_for_update()
        .prefetch_related("default_parts__part")
        .get(pk=service.pk)
    )

    quantity = normalize_service_quantity(quantity)

    if quantity <= Decimal("0.00"):
        raise ValidationError("A quantidade deve ser maior que zero.")

    if unit_price in [None, ""]:
        unit_price = normalize_service_money(service.default_price)
    else:
        unit_price = normalize_service_money(unit_price)

    if unit_price < Decimal("0.00"):
        raise ValidationError("O preço unitário não pode ser negativo.")

    service_order_item = _create_order_service_item(
        service_order=service_order,
        service=service,
        quantity=quantity,
        unit_price=unit_price,
    )

    parts = _copy_default_parts_to_order_service(
        service_order=service_order,
        service_order_item=service_order_item,
        service=service,
        service_quantity=quantity,
        created_by=created_by,
    )

    return {
        "service_item": service_order_item,
        "parts": parts,
    }


@transaction.atomic
def add_combo_to_order(
    *,
    service_order,
    combo,
    quantity=Decimal("1.00"),
    created_by=None,
):
    validate_order_can_receive_services(service_order)
    validate_active_combo(combo)

    combo = (
        ServiceCombo.objects.select_for_update()
        .prefetch_related(
            "items__service",
            "items__service__default_parts",
            "items__service__default_parts__part",
        )
        .get(pk=combo.pk)
    )

    validate_combo_has_items(combo)

    combo_quantity = normalize_service_quantity(quantity)

    if combo_quantity <= Decimal("0.00"):
        raise ValidationError(
            {"quantity": "A quantidade do combo deve ser maior que zero."}
        )

    discount_amount = normalize_service_money(combo.discount_amount * combo_quantity)

    combo_lines = _get_combo_lines(
        combo=combo,
        combo_quantity=combo_quantity,
    )

    discounted_lines = _apply_combo_discount_to_lines(
        lines=combo_lines,
        discount_amount=discount_amount,
    )

    created_items = []
    created_parts = []

    for line in discounted_lines:
        service = line["service"]
        service_quantity = line["quantity"]
        unit_price = line["final_unit_price"]

        service_order_item = _create_order_service_item(
            service_order=service_order,
            service=service,
            quantity=service_quantity,
            unit_price=unit_price,
            prefix=f"[Combo: {combo.name}] ",
        )

        parts = _copy_default_parts_to_order_service(
            service_order=service_order,
            service_order_item=service_order_item,
            service=service,
            service_quantity=service_quantity,
            created_by=created_by,
        )

        created_items.append(service_order_item)
        created_parts.extend(parts)

    return created_items
