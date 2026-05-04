from django.db import IntegrityError, transaction
from django.utils import timezone

from core.exceptions import FinancialAmountError, ObjectAlreadyExistsError
from service_orders.models import ServiceOrder
from service_orders.selectors import get_service_order_financial_summary

from .models import (
    CashFlowEntry,
    CashFlowType,
    Expense,
    Payment,
    PaymentStatus,
    Receivable,
)


@transaction.atomic
def create_receivable_from_service_order(service_order, created_by, due_date=None):
    """
    Create a receivable from the public service order financial summary.
    """
    if service_order.status != ServiceOrder.Status.FINISHED:
        raise FinancialAmountError(
            "A conta a receber só pode ser criada para uma OS finalizada."
        )

    if Receivable.objects.filter(service_order=service_order).exists():
        raise ObjectAlreadyExistsError(
            "Esta ordem de serviço já possui uma conta a receber."
        )

    summary = get_service_order_financial_summary(service_order)

    receivable = Receivable(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=summary["gross_total"],
        discount_amount=summary["discount"],
        final_amount=summary["net_total"],
        due_date=due_date,
        created_by=created_by,
    )

    receivable.full_clean()

    try:
        receivable.save()
    except IntegrityError as exc:
        raise ObjectAlreadyExistsError(
            "Esta ordem de serviço já possui uma conta a receber."
        ) from exc

    return receivable


@transaction.atomic
def register_payment(receivable, amount, method, created_by, paid_at=None, notes=None):
    """
    Register a payment and create a cash flow income entry.
    """
    locked_receivable = (
        Receivable.objects.select_for_update()
        .select_related("service_order", "customer")
        .get(pk=receivable.pk)
    )

    if locked_receivable.status == PaymentStatus.CANCELED:
        raise FinancialAmountError("Não é possível pagar uma conta cancelada.")

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
    description,
    amount,
    created_by,
    due_date=None,
    paid_at=None,
    notes=None,
):
    """
    Register an expense and create cash flow entry when already paid.
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
def mark_expense_as_paid(expense, paid_at=None, user=None):
    """
    Mark an expense as paid and create a cash flow expense entry.
    """
    locked_expense = Expense.objects.select_for_update().get(pk=expense.pk)

    if locked_expense.status == PaymentStatus.PAID:
        return locked_expense

    locked_expense.status = PaymentStatus.PAID
    locked_expense.paid_at = paid_at or timezone.now()
    locked_expense.full_clean()
    locked_expense.save(update_fields=["status", "paid_at", "updated_at"])

    CashFlowEntry.objects.create(
        entry_type=CashFlowType.EXPENSE,
        description=locked_expense.description,
        amount=locked_expense.amount,
        expense=locked_expense,
        created_by=user or locked_expense.created_by,
    )

    return locked_expense
