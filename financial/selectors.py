from django.db.models import Sum

from .models import CashFlowEntry, CashFlowType, Expense, PaymentStatus, Receivable


def get_pending_receivables():
    """
    Return pending receivables.
    """
    return Receivable.objects.filter(status=PaymentStatus.PENDING).select_related(
        "customer",
        "service_order",
    )


def get_paid_receivables():
    """
    Return paid receivables.
    """
    return Receivable.objects.filter(status=PaymentStatus.PAID).select_related(
        "customer",
        "service_order",
    )


def get_pending_expenses():
    """
    Return pending expenses.
    """
    return Expense.objects.filter(status=PaymentStatus.PENDING)


def get_cash_flow_summary():
    """
    Return income, expense and balance totals.
    """
    income = (
        CashFlowEntry.objects.filter(entry_type=CashFlowType.INCOME).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    expense = (
        CashFlowEntry.objects.filter(entry_type=CashFlowType.EXPENSE).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
    }


def get_cash_flow_entries():
    """
    Return cash flow entries.
    """
    return CashFlowEntry.objects.select_related(
        "payment",
        "expense",
        "created_by",
    )