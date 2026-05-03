from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
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
from financial.selectors import (
    get_cash_flow_summary,
    get_pending_expenses,
    get_pending_receivables,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="financial_selectors@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def order(user):
    customer = Customer.objects.create(name="Cliente Selector", phone="11999999999")
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="FIN-0003",
        brand="GM",
        model="Corsa",
    )
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS",
        description="Teste",
    )


@pytest.mark.django_db
def test_get_pending_receivables_returns_only_pending(order, user):
    pending = Receivable.objects.create(
        service_order=order,
        customer=order.customer,
        original_amount=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("10.00"),
        status=PaymentStatus.PENDING,
        created_by=user,
    )

    assert list(get_pending_receivables()) == [pending]


@pytest.mark.django_db
def test_get_pending_expenses_returns_only_pending(user):
    pending = Expense.objects.create(
        description="Pendente",
        amount=Decimal("10.00"),
        status=PaymentStatus.PENDING,
        created_by=user,
    )
    Expense.objects.create(
        description="Paga",
        amount=Decimal("10.00"),
        status=PaymentStatus.PAID,
        created_by=user,
    )

    assert list(get_pending_expenses()) == [pending]


@pytest.mark.django_db
def test_get_cash_flow_summary_calculates_income_expense_and_balance(order, user):

    receivable = Receivable.objects.create(
        service_order=order,
        customer=order.customer,
        original_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("100.00"),
        paid_amount=Decimal("100.00"),
        status=PaymentStatus.PAID,
        created_by=user,
    )

    payment = Payment.objects.create(
        receivable=receivable,
        amount=Decimal("100.00"),
        method=PaymentMethod.PIX,
        paid_at=timezone.now(),
        created_by=user,
    )

    CashFlowEntry.objects.create(
        entry_type=CashFlowType.INCOME,
        description="Entrada",
        amount=Decimal("100.00"),
        payment=payment,
        created_by=user,
    )
    expense = Expense.objects.create(
        description="Despesa teste",
        amount=Decimal("40.00"),
        status=PaymentStatus.PAID,
        paid_at=timezone.now(),
        created_by=user,
    )

    CashFlowEntry.objects.create(
        entry_type=CashFlowType.EXPENSE,
        description="Saída",
        amount=Decimal("40.00"),
        expense=expense,
        created_by=user,
    )

    assert get_cash_flow_summary() == {
        "income": Decimal("100.00"),
        "expense": Decimal("40.00"),
        "balance": Decimal("60.00"),
    }
