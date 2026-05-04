from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from .models import CashFlowEntry, CashFlowType, Expense, PaymentStatus, Receivable


def get_receivable_by_id(receivable_id):
    """
    Return one receivable with common relationships loaded.
    """
    return Receivable.objects.select_related(
        "customer",
        "service_order",
        "created_by",
    ).get(pk=receivable_id)


def get_receivables_for_list(search=None, status=None):
    """
    Return receivables filtered for the list screen.
    """
    queryset = Receivable.objects.select_related(
        "customer",
        "service_order",
        "created_by",
    ).order_by("due_date", "-created_at")

    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(
            Q(customer__name__icontains=search)
            | Q(customer__document__icontains=search)
            | Q(service_order__title__icontains=search)
            | Q(service_order__vehicle__plate__icontains=search)
        )

    return queryset


def get_pending_receivables():
    """
    Return pending receivables.
    """
    return get_receivables_for_list(status=PaymentStatus.PENDING)


def get_paid_receivables():
    """
    Return paid receivables.
    """
    return get_receivables_for_list(status=PaymentStatus.PAID)


def get_expense_by_id(expense_id):
    """
    Return one expense with user relationship loaded.
    """
    return Expense.objects.select_related("created_by").get(pk=expense_id)


def get_expenses_for_list(search=None, status=None):
    """
    Return expenses filtered for the list screen.
    """
    queryset = Expense.objects.select_related("created_by").order_by(
        "due_date",
        "-created_at",
    )

    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(description__icontains=search)

    return queryset


def get_pending_expenses():
    """
    Return pending expenses.
    """
    return get_expenses_for_list(status=PaymentStatus.PENDING)


def get_cash_flow_summary(start_date=None, end_date=None):
    """
    Return income, expense and balance totals for an optional period.
    """
    queryset = CashFlowEntry.objects.all()

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    income = queryset.filter(entry_type=CashFlowType.INCOME).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    expense = queryset.filter(entry_type=CashFlowType.EXPENSE).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    pending_receivables = Receivable.objects.filter(
        status=PaymentStatus.PENDING
    ).aggregate(total=Sum("final_amount") - Sum("paid_amount"))["total"] or Decimal(
        "0.00"
    )

    pending_expenses = Expense.objects.filter(status=PaymentStatus.PENDING).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "pending_receivables": pending_receivables,
        "pending_expenses": pending_expenses,
    }


def get_cash_flow_entries(start_date=None, end_date=None):
    """
    Return cash flow entries filtered by optional period.
    """
    queryset = CashFlowEntry.objects.select_related(
        "payment",
        "payment__receivable",
        "payment__receivable__customer",
        "expense",
        "created_by",
    ).order_by("-created_at")

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    return queryset


def get_financial_dashboard_data(filters=None):
    """
    Return all data needed by the financial dashboard.
    """
    filters = filters or {}
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")

    return {
        "summary": get_cash_flow_summary(start_date=start_date, end_date=end_date),
        "pending_receivables": get_pending_receivables()[:10],
        "pending_expenses": get_pending_expenses()[:10],
        "cash_flow_entries": get_cash_flow_entries(
            start_date=start_date,
            end_date=end_date,
        )[:20],
        "today": timezone.localdate(),
    }
