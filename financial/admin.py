from django.contrib import admin

from .models import CashFlowEntry, Expense, Payment, Receivable


@admin.register(Receivable)
class ReceivableAdmin(admin.ModelAdmin):
    """
    Admin configuration for receivables.
    """

    list_display = (
        "service_order",
        "customer",
        "final_amount",
        "paid_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "customer__name",
        "service_order__title",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for payments.
    """

    list_display = (
        "receivable",
        "amount",
        "method",
        "paid_at",
        "created_by",
    )
    list_filter = ("method", "paid_at")
    search_fields = (
        "receivable__customer__name",
        "receivable__service_order__title",
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Admin configuration for expenses.
    """

    list_display = (
        "description",
        "amount",
        "status",
        "due_date",
        "paid_at",
        "created_by",
    )
    list_filter = ("status", "due_date", "paid_at")
    search_fields = ("description",)


@admin.register(CashFlowEntry)
class CashFlowEntryAdmin(admin.ModelAdmin):
    """
    Admin configuration for cash flow entries.
    """

    list_display = (
        "entry_type",
        "description",
        "amount",
        "created_by",
        "created_at",
    )
    list_filter = ("entry_type", "created_at")
    search_fields = ("description",)