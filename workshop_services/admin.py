from django.contrib import admin

from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopCatalogAuditLog,
    WorkshopService,
    WorkshopServiceCategory,
    WorkshopServicePart,
    WorkshopServiceVersion,
)


@admin.register(WorkshopServiceCategory)
class WorkshopServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "description", "parent__name"]


class WorkshopServicePartInline(admin.TabularInline):
    model = WorkshopServicePart
    extra = 1


class WorkshopServiceVersionInline(admin.TabularInline):
    model = WorkshopServiceVersion
    extra = 0
    readonly_fields = [
        "version_number",
        "code_snapshot",
        "name_snapshot",
        "category_snapshot",
        "default_price_snapshot",
        "estimated_minutes_snapshot",
        "parts_snapshot",
        "created_by",
        "created_at",
    ]
    can_delete = False


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
        "current_version",
        "is_active",
    ]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "code", "category__name"]
    readonly_fields = ["current_version"]
    inlines = [WorkshopServicePartInline, WorkshopServiceVersionInline]


@admin.register(WorkshopServiceVersion)
class WorkshopServiceVersionAdmin(admin.ModelAdmin):
    list_display = ["service", "version_number", "default_price_snapshot", "estimated_minutes_snapshot", "created_by", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["service__name", "service__code", "name_snapshot", "code_snapshot"]
    readonly_fields = [
        "service",
        "version_number",
        "code_snapshot",
        "name_snapshot",
        "category_snapshot",
        "description_snapshot",
        "default_price_snapshot",
        "estimated_minutes_snapshot",
        "parts_snapshot",
        "created_by",
        "created_at",
    ]


@admin.register(ServiceCombo)
class ServiceComboAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "discount_amount", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    inlines = [ServiceComboItemInline]


@admin.register(WorkshopCatalogAuditLog)
class WorkshopCatalogAuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "service", "combo", "category", "changed_by", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["service__name", "service__code", "combo__name", "combo__code", "category__name"]
    readonly_fields = ["action", "service", "combo", "category", "changed_by", "old_data", "new_data", "created_at"]
