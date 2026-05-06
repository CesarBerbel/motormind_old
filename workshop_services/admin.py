from django.contrib import admin

from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopService,
    WorkshopServicePart,
)


class WorkshopServicePartInline(admin.TabularInline):
    model = WorkshopServicePart
    extra = 1


class ServiceComboItemInline(admin.TabularInline):
    model = ServiceComboItem
    extra = 1


@admin.register(WorkshopService)
class WorkshopServiceAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "category",
        "default_price",
        "estimated_minutes",
        "is_active",
    ]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "code", "category"]
    inlines = [WorkshopServicePartInline]


@admin.register(ServiceCombo)
class ServiceComboAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "discount_amount", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    inlines = [ServiceComboItemInline]
