from django.contrib import admin

from .models import (
    ServiceOrder,
    ServiceOrderHistory,
    ServiceOrderItem,
    ServiceOrderNote,
)


class ServiceOrderItemInline(admin.TabularInline):
    """
    Inline admin to show service order items.
    """

    model = ServiceOrderItem
    extra = 0


class ServiceOrderNoteInline(admin.TabularInline):
    """
    Inline admin to show service order notes.
    """

    model = ServiceOrderNote
    extra = 0
    readonly_fields = (
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
        "id",
        "customer",
        "vehicle",
        "assigned_mechanic",
        "title",
        "status",
        "total_amount",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "assigned_mechanic",
        "created_at",
        "expected_delivery_date",
    )

    search_fields = (
        "customer__name",
        "vehicle__plate",
        "assigned_mechanic__email",
        "title",
        "description",
    )

    readonly_fields = (
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
        ServiceOrderItemInline,
        ServiceOrderNoteInline,
        ServiceOrderHistoryInline,
    ]

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "customer",
                    "vehicle",
                    "created_by",
                    "assigned_mechanic",
                    "title",
                    "status",
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
class ServiceOrderNoteAdmin(admin.ModelAdmin):
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
