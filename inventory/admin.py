from django.contrib import admin

from .models import Part, StockMovement


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    """
    Admin configuration for inventory parts.
    """

    list_display = (
        "internal_code",
        "name",
        "brand",
        "category",
        "current_stock",
        "minimum_stock",
        "stock_status_label",
        "sale_price",
        "is_active",
    )

    list_filter = (
        "is_active",
        "brand",
        "category",
        "created_at",
    )

    search_fields = (
        "name",
        "internal_code",
        "barcode",
        "brand",
        "category",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "stock_status_label",
    )

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "name",
                    "internal_code",
                    "barcode",
                    "brand",
                    "category",
                    "unit",
                    "location",
                    "is_active",
                )
            },
        ),
        (
            "Valores",
            {
                "fields": (
                    "cost_price",
                    "sale_price",
                )
            },
        ),
        (
            "Estoque",
            {
                "fields": (
                    "current_stock",
                    "minimum_stock",
                    "stock_status_label",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """
    Admin configuration for stock movements.
    """

    list_display = (
        "part",
        "movement_type",
        "quantity",
        "unit_cost",
        "unit_sale_price",
        "service_order",
        "created_by",
        "created_at",
    )

    list_filter = (
        "movement_type",
        "created_at",
        "part__brand",
        "part__category",
    )

    search_fields = (
        "part__name",
        "part__internal_code",
        "reason",
        "created_by__email",
    )

    autocomplete_fields = (
        "part",
        "service_order",
        "created_by",
    )

    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Movimentação",
            {
                "fields": (
                    "part",
                    "movement_type",
                    "quantity",
                    "unit_cost",
                    "unit_sale_price",
                    "reason",
                    "service_order",
                    "created_by",
                )
            },
        ),
        (
            "Controle",
            {"fields": ("created_at",)},
        ),
    )
