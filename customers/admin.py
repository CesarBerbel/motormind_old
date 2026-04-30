from django.contrib import admin

from .models import Customer, Vehicle


class VehicleInline(admin.TabularInline):
    """
    Inline admin to show vehicles inside customer page.
    """

    model = Vehicle
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin configuration for customers.
    """

    list_display = (
        "name",
        "phone",
        "email",
        "document",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "email",
        "document",
    )

    ordering = ("name",)

    inlines = [
        VehicleInline,
    ]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Admin configuration for vehicles.
    """

    list_display = (
        "plate",
        "brand",
        "model",
        "customer",
        "mileage",
        "is_active",
    )

    list_filter = (
        "brand",
        "is_active",
        "created_at",
    )

    search_fields = (
        "plate",
        "brand",
        "model",
        "customer__name",
    )

    autocomplete_fields = ("customer",)

    ordering = ("plate",)
