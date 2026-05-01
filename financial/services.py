from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import (
    CashFlowEntry,
    CashFlowType,
    Expense,
    Payment,
    PaymentStatus,
    Receivable,
)


@transaction.atomic
def create_receivable_from_service_order(service_order, created_by):
    """
    Create a receivable from a service order total.
    """
    original_amount = service_order.total_amount
    discount_amount = service_order.discount
    final_amount = original_amount - discount_amount

    if final_amount < Decimal("0.00"):
        final_amount = Decimal("0.00")

    receivable = Receivable(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=original_amount,
        discount_amount=discount_amount,
        final_amount=final_amount,
        created_by=created_by,
    )

    receivable.full_clean()
    receivable.save()

    return receivable


@transaction.atomic
def register_payment(receivable, amount, method, created_by, paid_at=None, notes=None):
    """
    Register a payment and create a cash flow income entry.

    This function locks the receivable row to avoid concurrent payments
    updating paid_amount with stale data.
    """
    locked_receivable = (
        Receivable.objects.select_for_update()
        .select_related("service_order", "customer")
        .get(pk=receivable.pk)
    )

    payment = Payment(
        receivable=locked_receivable,
        amount=amount,
        method=method,
        paid_at=paid_at or timezone.now(),
        notes=notes,
        created_by=created_by,
    )

    payment.full_clean()
    payment.save()

    locked_receivable.paid_amount += payment.amount

    if locked_receivable.paid_amount >= locked_receivable.final_amount:
        locked_receivable.status = PaymentStatus.PAID
    else:
        locked_receivable.status = PaymentStatus.PENDING

    locked_receivable.full_clean()
    locked_receivable.save(update_fields=["paid_amount", "status", "updated_at"])

    CashFlowEntry.objects.create(
        entry_type=CashFlowType.INCOME,
        description=f"Pagamento da OS #{locked_receivable.service_order_id}",
        amount=payment.amount,
        payment=payment,
        created_by=created_by,
    )

    return payment


@transaction.atomic
def register_expense(
    description, amount, created_by, due_date=None, paid_at=None, notes=None
):
    """
    Register an expense and optionally create a cash flow expense entry if already paid.
    """
    status = PaymentStatus.PAID if paid_at else PaymentStatus.PENDING

    expense = Expense(
        description=description,
        amount=amount,
        due_date=due_date,
        paid_at=paid_at,
        status=status,
        notes=notes,
        created_by=created_by,
    )

    expense.full_clean()
    expense.save()

    if paid_at:
        CashFlowEntry.objects.create(
            entry_type=CashFlowType.EXPENSE,
            description=expense.description,
            amount=expense.amount,
            expense=expense,
            created_by=created_by,
        )

    return expense


@transaction.atomic
def mark_expense_as_paid(expense, paid_at, user):
    """
    Mark an expense as paid and create a cash flow expense entry.

    This function locks the expense row to avoid two concurrent requests
    creating duplicated cash flow entries for the same expense.
    """
    locked_expense = Expense.objects.select_for_update().get(pk=expense.pk)

    if locked_expense.status == PaymentStatus.PAID:
        return locked_expense

    locked_expense.status = PaymentStatus.PAID
    locked_expense.paid_at = paid_at
    locked_expense.full_clean()
    locked_expense.save(update_fields=["status", "paid_at", "updated_at"])

    CashFlowEntry.objects.create(
        entry_type=CashFlowType.EXPENSE,
        description=locked_expense.description,
        amount=locked_expense.amount,
        expense=locked_expense,
        created_by=user,
    )

    return locked_expense
