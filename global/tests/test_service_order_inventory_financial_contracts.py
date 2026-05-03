from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from customers.models import Customer, Vehicle
from financial.models import PaymentStatus, Receivable
from financial.services import create_receivable_from_service_order
from inventory.forms import ServiceOrderPartForm
from inventory.models import Part, ServiceOrderPart, StockMovement
from inventory.services import (
    cancel_reserved_service_order_part,
    confirm_service_order_part_usage,
    reserve_part_for_service_order,
    return_used_service_order_part,
)
from service_orders.models import ServiceOrder, ServiceOrderItem
from service_orders.selectors import get_service_order_financial_summary


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="integration_contracts@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def service_order(user):
    customer = Customer.objects.create(
        name="Cliente Integração",
        phone="11999999999",
    )
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="INT-1000",
        brand="Fiat",
        model="Uno",
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS integração",
        description="Contrato ordem, estoque e financeiro.",
        labor_cost=Decimal("50.00"),
        parts_cost=Decimal("20.00"),
        discount=Decimal("15.00"),
    )
    ServiceOrderItem.objects.create(
        service_order=order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description="Diagnóstico",
        quantity=Decimal("1.00"),
        unit_price=Decimal("100.00"),
    )
    return order


@pytest.fixture
def part():
    return Part.objects.create(
        name="Filtro de óleo integração",
        internal_code="INT-OIL-001",
        brand="Mann",
        category="Motor",
        unit="un",
        cost_price=Decimal("20.00"),
        sale_price=Decimal("45.00"),
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("2.00"),
    )


def reserve_part(order, part, user, quantity="2.00", unit_price="45.00", discount="0.00"):
    form = ServiceOrderPartForm(
        data={
            "part": part.pk,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount,
        }
    )
    assert form.is_valid(), form.errors
    return reserve_part_for_service_order(
        service_order=order,
        form=form,
        created_by=user,
    )


@pytest.mark.django_db
def test_reserving_inventory_part_updates_stock_movement_and_order_summary(
    service_order, part, user
):
    service_order_part = reserve_part(service_order, part, user)

    part.refresh_from_db()
    summary = get_service_order_financial_summary(service_order)

    assert service_order_part.status == ServiceOrderPart.Status.RESERVED
    assert part.current_stock == Decimal("8.00")
    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RESERVE,
        quantity=Decimal("2.00"),
    ).exists()
    assert summary["manual_services_total"] == Decimal("100.00")
    assert summary["inventory_parts_total"] == Decimal("90.00")
    assert summary["gross_total"] == Decimal("260.00")
    assert summary["discount"] == Decimal("15.00")
    assert summary["net_total"] == Decimal("245.00")


@pytest.mark.django_db
def test_canceling_reserved_inventory_part_releases_stock_and_excludes_from_summary(
    service_order, part, user
):
    service_order_part = reserve_part(service_order, part, user)

    cancel_reserved_service_order_part(
        service_order_part=service_order_part,
        changed_by=user,
    )

    service_order_part.refresh_from_db()
    part.refresh_from_db()
    summary = get_service_order_financial_summary(service_order)

    assert service_order_part.status == ServiceOrderPart.Status.CANCELED
    assert part.current_stock == Decimal("10.00")
    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RELEASE,
        quantity=Decimal("2.00"),
    ).exists()
    assert summary["inventory_parts_total"] == Decimal("0.00")
    assert summary["gross_total"] == Decimal("170.00")
    assert summary["net_total"] == Decimal("155.00")


@pytest.mark.django_db
def test_confirmed_used_inventory_part_is_billable_and_receivable_uses_single_summary(
    service_order, part, user
):
    service_order_part = reserve_part(service_order, part, user)
    confirm_service_order_part_usage(service_order_part=service_order_part)

    part.refresh_from_db()
    service_order_part.refresh_from_db()
    summary = get_service_order_financial_summary(service_order)
    receivable = create_receivable_from_service_order(service_order, user)

    assert service_order_part.status == ServiceOrderPart.Status.USED
    assert part.current_stock == Decimal("8.00")
    assert summary["inventory_parts_total"] == Decimal("90.00")
    assert receivable.customer == service_order.customer
    assert receivable.original_amount == summary["gross_total"] == Decimal("260.00")
    assert receivable.discount_amount == summary["discount"] == Decimal("15.00")
    assert receivable.final_amount == summary["net_total"] == Decimal("245.00")
    assert receivable.status == PaymentStatus.PENDING
    assert Receivable.objects.filter(service_order=service_order).count() == 1


@pytest.mark.django_db
def test_returning_used_inventory_part_restores_stock_excludes_total_and_blocks_duplicate(
    service_order, part, user
):
    service_order_part = reserve_part(service_order, part, user)
    confirm_service_order_part_usage(service_order_part=service_order_part)

    return_used_service_order_part(
        service_order_part=service_order_part,
        changed_by=user,
    )

    service_order_part.refresh_from_db()
    part.refresh_from_db()
    summary = get_service_order_financial_summary(service_order)

    assert service_order_part.status == ServiceOrderPart.Status.RETURNED
    assert part.current_stock == Decimal("10.00")
    assert summary["inventory_parts_total"] == Decimal("0.00")
    assert summary["gross_total"] == Decimal("170.00")
    assert summary["net_total"] == Decimal("155.00")
    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RETURN,
        quantity=Decimal("2.00"),
    ).count() == 1

    with pytest.raises(ValidationError):
        return_used_service_order_part(
            service_order_part=service_order_part,
            changed_by=user,
        )

    part.refresh_from_db()
    assert part.current_stock == Decimal("10.00")
    assert StockMovement.objects.filter(
        part=part,
        service_order=service_order,
        movement_type=StockMovement.MovementType.RETURN,
    ).count() == 1
