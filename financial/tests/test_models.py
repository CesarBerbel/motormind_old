from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from customers.models import Customer, Vehicle
from financial.models import (
    CashFlowEntry,
    CashFlowType,
    Expense,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Receivable,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="financial_models@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def service_order(user):
    customer = Customer.objects.create(name="Cliente Financeiro", phone="11999999999")
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="FIN-0001",
        brand="VW",
        model="Gol",
    )
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS financeira",
        description="Validar financeiro.",
    )


@pytest.mark.django_db
def test_receivable_remaining_amount_never_negative(service_order, user):
    receivable = Receivable.objects.create(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("100.00"),
        paid_amount=Decimal("120.00"),
        created_by=user,
    )

    assert receivable.remaining_amount == Decimal("0.00")
    assert receivable.is_fully_paid is True


@pytest.mark.django_db
def test_receivable_clean_rejects_discount_greater_than_original(service_order, user):
    receivable = Receivable(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=Decimal("100.00"),
        discount_amount=Decimal("120.00"),
        final_amount=Decimal("0.00"),
        created_by=user,
    )

    with pytest.raises(ValidationError):
        receivable.full_clean()


@pytest.mark.django_db
def test_cash_flow_entry_requires_exactly_one_origin(user):
    entry = CashFlowEntry(
        entry_type=CashFlowType.INCOME,
        description="Entrada sem origem",
        amount=Decimal("10.00"),
        created_by=user,
    )

    with pytest.raises(ValidationError):
        entry.full_clean()


@pytest.mark.django_db
def test_cash_flow_entry_cannot_have_payment_and_expense(service_order, user):
    receivable = Receivable.objects.create(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("100.00"),
        created_by=user,
    )
    expense = Expense.objects.create(
        description="Despesa indevida",
        amount=Decimal("10.00"),
        status=PaymentStatus.PENDING,
        created_by=user,
    )
    payment = Payment.objects.create(
        receivable=receivable,
        amount=Decimal("10.00"),
        method=PaymentMethod.PIX,
        paid_at=timezone.now(),
        created_by=user,
    )

    entry = CashFlowEntry(
        entry_type=CashFlowType.INCOME,
        description="Origem duplicada",
        amount=Decimal("10.00"),
        payment=payment,
        expense=expense,
        created_by=user,
    )

    with pytest.raises(ValidationError):
        entry.full_clean()
