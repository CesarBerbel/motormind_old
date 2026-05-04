from django.contrib import admin

from .models import (
    ServiceOrder,
    ServiceOrderApproval,
    ServiceOrderHistory,
    ServiceOrderItem,
    ServiceOrderNote,
    ServiceOrderTimeEntry,
)


class ServiceOrderRelatedNumberMixin:
    """
    Helper used by admin classes for models that are linked to a service order.
    """

    @admin.display(description="Número da OS")
    def service_order_number(self, obj):
        """
        Return the public service order number for related records.
        """
        if not obj or not getattr(obj, "service_order", None):
            return "-"

        return obj.service_order.display_number


class ServiceOrderApprovalInline(ServiceOrderRelatedNumberMixin, admin.StackedInline):
    """
    Inline admin to show formal budget approval.
    """

    model = ServiceOrderApproval
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = (
        "approved_by",
        "customer_name_snapshot",
        "vehicle_snapshot",
        "gross_total",
        "discount",
        "net_total",
        "financial_summary_snapshot",
        "approved_at",
        "service_order_number",
        "created_at",
        "updated_at",
    )


class ServiceOrderItemInline(admin.TabularInline):
    """
    Inline admin to show service order items.
    """

    model = ServiceOrderItem
    extra = 0


class ServiceOrderNoteInline(ServiceOrderRelatedNumberMixin, admin.TabularInline):
    """
    Inline admin to show service order notes.
    """

    model = ServiceOrderNote
    extra = 0
    readonly_fields = (
        "service_order_number",
        "created_at",
        "updated_at",
    )


class ServiceOrderTimeEntryInline(ServiceOrderRelatedNumberMixin, admin.TabularInline):
    """
    Inline admin to show time entries.
    """

    model = ServiceOrderTimeEntry
    extra = 0
    readonly_fields = (
        "started_at",
        "ended_at",
        "service_order_number",
        "created_at",
        "updated_at",
    )


class ServiceOrderHistoryInline(admin.TabularInline):
    """
    Inline admin to show service order audit history.
    """

    model = ServiceOrderHistory
    extra = 0
    can_delete = False

    readonly_fields = (
        "changed_by",
        "field_name",
        "old_value",
        "new_value",
        "created_at",
    )

    fields = (
        "created_at",
        "changed_by",
        "field_name",
        "old_value",
        "new_value",
    )

    def has_add_permission(self, request, obj=None):
        """
        Disable manual history creation in admin.
        """
        return False


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for service orders.
    """

    list_display = (
        "number",
        "id",
        "customer",
        "vehicle",
        "assigned_mechanic",
        "title",
        "status",
        "priority",
        "total_amount",
        "is_budget_approved",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "assigned_mechanic",
        "created_at",
        "expected_delivery_date",
    )

    search_fields = (
        "number",
        "customer__name",
        "vehicle__plate",
        "assigned_mechanic__email",
        "title",
        "description",
    )

    readonly_fields = (
        "number",
        "created_at",
        "updated_at",
        "finished_at",
        "total_amount",
    )

    autocomplete_fields = (
        "customer",
        "vehicle",
        "created_by",
        "assigned_mechanic",
    )

    ordering = ("-created_at",)

    inlines = [
        ServiceOrderApprovalInline,
        ServiceOrderItemInline,
        ServiceOrderNoteInline,
        ServiceOrderHistoryInline,
        ServiceOrderTimeEntryInline,
    ]

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "number",
                    "customer",
                    "vehicle",
                    "created_by",
                    "assigned_mechanic",
                    "title",
                    "status",
                    "priority",
                )
            },
        ),
        (
            "Informações técnicas",
            {
                "fields": (
                    "description",
                    "diagnosis",
                    "solution",
                )
            },
        ),
        (
            "Valores",
            {
                "fields": (
                    "labor_cost",
                    "parts_cost",
                    "discount",
                    "total_amount",
                )
            },
        ),
        (
            "Datas",
            {
                "fields": (
                    "expected_delivery_date",
                    "finished_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(ServiceOrderItem)
class ServiceOrderItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for service order items.
    """

    list_display = (
        "service_order",
        "item_type",
        "description",
        "quantity",
        "unit_price",
        "total",
    )

    list_filter = (
        "item_type",
        "created_at",
    )

    search_fields = (
        "description",
        "service_order__title",
        "service_order__customer__name",
    )


@admin.register(ServiceOrderNote)
class ServiceOrderNoteAdmin(ServiceOrderRelatedNumberMixin, admin.ModelAdmin):
    """
    Admin configuration for service order notes.
    """

    list_display = (
        "service_order",
        "note_type",
        "created_by",
        "created_at",
    )

    list_filter = (
        "note_type",
        "created_at",
    )

    search_fields = (
        "text",
        "service_order__title",
        "service_order__customer__name",
        "created_by__email",
    )

    readonly_fields = (
        "service_order_number",
        "created_at",
        "updated_at",
    )


@admin.register(ServiceOrderHistory)
class ServiceOrderHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for service order history.
    """

    list_display = (
        "service_order",
        "field_name",
        "changed_by",
        "created_at",
    )

    list_filter = (
        "field_name",
        "created_at",
    )

    search_fields = (
        "service_order__title",
        "service_order__customer__name",
        "changed_by__email",
        "field_name",
        "old_value",
        "new_value",
    )

    readonly_fields = (
        "service_order",
        "changed_by",
        "field_name",
        "old_value",
        "new_value",
        "created_at",
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        """
        Disable manual history creation.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Disable manual history editing.
        """
        return False


@admin.register(ServiceOrderTimeEntry)
class ServiceOrderTimeEntryAdmin(ServiceOrderRelatedNumberMixin, admin.ModelAdmin):
    """
    Admin configuration for service order time entries.
    """

    list_display = (
        "service_order",
        "mechanic",
        "started_at",
        "ended_at",
        "is_open",
    )

    list_filter = (
        "started_at",
        "ended_at",
        "mechanic",
    )

    search_fields = (
        "service_order__title",
        "service_order__customer__name",
        "mechanic__email",
        "note",
    )

    readonly_fields = (
        "service_order_number",
        "created_at",
        "updated_at",
    )


@admin.register(ServiceOrderApproval)
class ServiceOrderApprovalAdmin(admin.ModelAdmin):
    """
    Admin configuration for service order budget approvals.
    """

    list_display = (
        "service_order",
        "channel",
        "net_total",
        "approved_by",
        "approved_at",
    )

    list_filter = (
        "channel",
        "approved_at",
    )

    search_fields = (
        "service_order__number",
        "service_order__customer__name",
        "customer_name_snapshot",
        "vehicle_snapshot",
    )

    readonly_fields = (
        "service_order",
        "approved_by",
        "customer_name_snapshot",
        "vehicle_snapshot",
        "gross_total",
        "discount",
        "net_total",
        "financial_summary_snapshot",
        "approved_at",
        "created_at",
        "updated_at",
    )
