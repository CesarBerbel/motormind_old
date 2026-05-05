from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderItem
from service_orders.selectors import get_service_order_financial_summary
from workshop_services.models import ServiceCombo, ServiceComboItem, WorkshopService
from workshop_services.services import add_catalog_service_to_order, add_combo_to_order


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(email="admin@test.com", password="test123456")


@pytest.fixture
def service_order(db, user):
    customer = baker.make(
        Customer,
        name="Cliente Teste",
        phone="11999999999",
        email="cliente@test.com",
        document="12345678900",
        is_active=True,
    )
    vehicle = baker.make(
        Vehicle,
        customer=customer,
        plate="ABC1234",
        brand="Ford",
        model="Fiesta",
        year=2020,
        mileage=10000,
        is_active=True,
    )
    return baker.make(
        ServiceOrder,
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Troca de óleo",
        description="Cliente solicitou revisão.",
    )


@pytest.mark.django_db
def test_add_catalog_service_to_order_uses_default_price(service_order):
    service = WorkshopService.objects.create(
        name="Alinhamento",
        code="SRV-001",
        default_price=Decimal("120.00"),
        estimated_minutes=60,
    )

    item = add_catalog_service_to_order(
        service_order=service_order,
        service=service,
        quantity=Decimal("2.00"),
    )

    assert item.item_type == ServiceOrderItem.ItemType.SERVICE
    assert item.description == "SRV-001 - Alinhamento"
    assert item.total == Decimal("240.0000")
    assert get_service_order_financial_summary(service_order)["net_total"] == Decimal("240.00")


@pytest.mark.django_db
def test_add_combo_to_order_creates_service_items_with_discount(service_order):
    service_1 = WorkshopService.objects.create(
        name="Troca de óleo",
        code="SRV-001",
        default_price=Decimal("100.00"),
    )
    service_2 = WorkshopService.objects.create(
        name="Filtro de ar",
        code="SRV-002",
        default_price=Decimal("50.00"),
    )
    combo = ServiceCombo.objects.create(
        name="Revisão básica",
        code="CMB-001",
        discount_amount=Decimal("30.00"),
    )
    ServiceComboItem.objects.create(
        combo=combo,
        service=service_1,
        quantity=Decimal("1.00"),
        unit_price=Decimal("100.00"),
    )
    ServiceComboItem.objects.create(
        combo=combo,
        service=service_2,
        quantity=Decimal("1.00"),
        unit_price=Decimal("50.00"),
    )

    items = add_combo_to_order(service_order=service_order, combo=combo)

    assert len(items) == 2
    assert service_order.items.count() == 2
    assert get_service_order_financial_summary(service_order)["net_total"] == Decimal("120.00")
