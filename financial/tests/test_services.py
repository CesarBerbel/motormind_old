from decimal import Decimal

import pytest

from customers.models import Customer, Vehicle
from financial.services import create_receivable_from_service_order
from service_orders.models import ServiceOrder, ServiceOrderItem
from service_orders.selectors import get_service_order_financial_summary


@pytest.fixture
def service_order(django_user_model):
    user = django_user_model.objects.create_user(
        email="financial-summary@example.com",
        password="StrongPassword123",
    )
    customer = Customer.objects.create(
        name="Cliente Financeiro",
        phone="11999999999",
    )
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="FIN1234",
        brand="Fiat",
        model="Uno",
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Resumo financeiro",
        description="Teste de fonte única de total.",
        labor_cost=Decimal("40.00"),
        parts_cost=Decimal("15.00"),
        discount=Decimal("25.00"),
    )
    ServiceOrderItem.objects.create(
        service_order=order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description="Serviço manual",
        quantity=Decimal("2.00"),
        unit_price=Decimal("50.00"),
    )
    ServiceOrderItem.objects.create(
        service_order=order,
        item_type=ServiceOrderItem.ItemType.PART,
        description="Peça avulsa",
        quantity=Decimal("1.00"),
        unit_price=Decimal("30.00"),
    )
    return order


@pytest.mark.django_db
def test_service_order_financial_summary_is_single_source_of_truth(service_order):
    summary = get_service_order_financial_summary(service_order)

    assert summary["manual_services_total"] == Decimal("100.00")
    assert summary["manual_parts_total"] == Decimal("30.00")
    assert summary["inventory_parts_total"] == Decimal("0.00")
    assert summary["labor_cost"] == Decimal("40.00")
    assert summary["extra_parts_cost"] == Decimal("15.00")
    assert summary["gross_total"] == Decimal("185.00")
    assert summary["discount"] == Decimal("25.00")
    assert summary["net_total"] == Decimal("160.00")
    assert service_order.total_amount == summary["net_total"]


@pytest.mark.django_db
def test_create_receivable_from_service_order_does_not_discount_twice(service_order):
    receivable = create_receivable_from_service_order(
        service_order=service_order,
        created_by=service_order.created_by,
    )

    assert receivable.original_amount == Decimal("185.00")
    assert receivable.discount_amount == Decimal("25.00")
    assert receivable.final_amount == Decimal("160.00")
