from django.contrib import admin

from .models import Part, PartBrand, PartCategory, ServiceOrderPart, StockMovement


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

    list_filter = ("is_active", "brand", "category", "created_at")
    search_fields = (
        "name",
        "internal_code",
        "barcode",
        "brand__name",
        "category__name",
    )
    readonly_fields = ("created_at", "updated_at", "stock_status_label")


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

    list_filter = ("movement_type", "created_at", "part__brand", "part__category")
    search_fields = ("part__name", "part__internal_code", "reason", "created_by__email")
    autocomplete_fields = ("part", "service_order", "created_by")
    readonly_fields = ("created_at",)


@admin.register(ServiceOrderPart)
class ServiceOrderPartAdmin(admin.ModelAdmin):
    """
    Admin configuration for service order parts.
    """

    list_display = (
        "service_order",
        "part",
        "quantity",
        "unit_price",
        "discount",
        "total",
        "status",
        "created_by",
        "created_at",
    )

    list_filter = ("status", "created_at", "part__brand", "part__category")
    search_fields = (
        "service_order__title",
        "service_order__customer__name",
        "part__name",
        "part__internal_code",
    )
    autocomplete_fields = ("service_order", "part", "created_by")
    readonly_fields = ("subtotal", "total", "created_at", "updated_at")


@admin.register(PartBrand)
class PartBrandAdmin(admin.ModelAdmin):
    """
    Admin configuration for part brands.
    """

    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for part categories.
    """

    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
