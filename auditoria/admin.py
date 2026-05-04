from django.contrib import admin

from auditoria.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "user",
        "app_label",
        "model_name",
        "object_id",
        "ip_address",
    )
    list_filter = (
        "action",
        "app_label",
        "model_name",
        "created_at",
    )
    search_fields = (
        "user__email",
        "object_repr",
        "object_id",
        "path",
        "ip_address",
    )
    readonly_fields = (
        "user",
        "action",
        "app_label",
        "model_name",
        "object_id",
        "object_repr",
        "content_type",
        "old_data",
        "new_data",
        "metadata",
        "ip_address",
        "user_agent",
        "path",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
