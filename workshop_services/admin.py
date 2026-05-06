from django.contrib import admin

from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopService,
    WorkshopServiceCategory,
    WorkshopServicePart,
)


@admin.register(WorkshopServiceCategory)
class WorkshopServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]


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
    search_fields = ["name", "code", "category__name"]
    inlines = [WorkshopServicePartInline]


@admin.register(ServiceCombo)
class ServiceComboAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "discount_amount", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    inlines = [ServiceComboItemInline]
