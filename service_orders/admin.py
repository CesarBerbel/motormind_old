from django.contrib import admin

from .models import ServiceOrder


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for service orders.
    """

    list_display = (
        "id",
        "customer",
        "vehicle",
        "title",
        "status",
        "total_amount",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
        "expected_delivery_date",
    )

    search_fields = (
        "customer__name",
        "vehicle__plate",
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
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "customer",
                    "vehicle",
                    "created_by",
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
