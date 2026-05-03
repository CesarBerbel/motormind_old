from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from customers.models import Customer, Vehicle
from financial.exceptions import FinancialError
from financial.models import (
    CashFlowEntry,
    CashFlowType,
    Expense,
    PaymentMethod,
    PaymentStatus,
)
from financial.services import (
    create_receivable_from_service_order,
    mark_expense_as_paid,
    register_expense,
    register_payment,
)
from service_orders.models import ServiceOrder, ServiceOrderItem


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="financial_services@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def service_order(user):
    customer = Customer.objects.create(name="Cliente Serviços", phone="11999999999")
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="FIN-0002",
        brand="Fiat",
        model="Uno",
    )
    order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS total",
        description="Total financeiro.",
        labor_cost=Decimal("50.00"),
        parts_cost=Decimal("20.00"),
        discount=Decimal("15.00"),
    )
    ServiceOrderItem.objects.create(
        service_order=order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description="Revisão",
        quantity=Decimal("1.00"),
        unit_price=Decimal("100.00"),
    )
    return order


@pytest.mark.django_db
def test_create_receivable_from_service_order_uses_gross_discount_and_net_once(
    service_order, user
):
    receivable = create_receivable_from_service_order(service_order, user)

    assert receivable.original_amount == Decimal("170.00")
    assert receivable.discount_amount == Decimal("15.00")
    assert receivable.final_amount == Decimal("155.00")

@pytest.mark.django_db
def test_register_partial_payment_keeps_receivable_pending(service_order, user):
    receivable = create_receivable_from_service_order(service_order, user)

    payment = register_payment(
        receivable,
        Decimal("55.00"),
        PaymentMethod.PIX,
        user,
    )

    receivable.refresh_from_db()

    assert payment.amount == Decimal("55.00")
    assert receivable.paid_amount == Decimal("55.00")
    assert receivable.status == PaymentStatus.PENDING
    assert CashFlowEntry.objects.filter(
        payment=payment,
        entry_type=CashFlowType.INCOME,
        amount=Decimal("55.00"),
    ).exists()


@pytest.mark.django_db
def test_register_full_payment_marks_receivable_paid(service_order, user):
    receivable = create_receivable_from_service_order(service_order, user)

    register_payment(
        receivable,
        receivable.final_amount,
        PaymentMethod.CASH,
        user,
    )

    receivable.refresh_from_db()

    assert receivable.status == PaymentStatus.PAID
    assert receivable.remaining_amount == Decimal("0.00")


@pytest.mark.django_db
def test_register_payment_rejects_amount_above_remaining(service_order, user):
    receivable = create_receivable_from_service_order(service_order, user)

    with pytest.raises(ValidationError):
        register_payment(
            receivable,
            receivable.final_amount + Decimal("0.01"),
            PaymentMethod.PIX,
            user,
        )


@pytest.mark.django_db
def test_register_paid_expense_creates_cash_flow_exit(user):
    paid_at = timezone.now()

    expense = register_expense(
        description="Aluguel",
        amount=Decimal("300.00"),
        created_by=user,
        paid_at=paid_at,
    )

    assert expense.status == PaymentStatus.PAID
    assert CashFlowEntry.objects.filter(
        expense=expense,
        entry_type=CashFlowType.EXPENSE,
        amount=Decimal("300.00"),
    ).exists()


@pytest.mark.django_db
def test_mark_expense_as_paid_is_idempotent(user):
    expense = Expense.objects.create(
        description="Energia",
        amount=Decimal("150.00"),
        status=PaymentStatus.PENDING,
        created_by=user,
    )

    mark_expense_as_paid(expense, timezone.now(), user)
    mark_expense_as_paid(expense, timezone.now(), user)

    expense.refresh_from_db()

    assert expense.status == PaymentStatus.PAID
    assert CashFlowEntry.objects.filter(expense=expense).count() == 1
