from django.contrib import admin

from .models import (
    MessageAttachment,
    MessageEvent,
    MessageLog,
    MessagePreference,
    MessageProvider,
    MessageQueue,
    MessageTemplate,
    MessageVariable,
)


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "channel", "message_type", "is_active"]
    list_filter = ["channel", "message_type", "is_active"]
    search_fields = ["name", "code", "subject", "body"]


@admin.register(MessageVariable)
class MessageVariableAdmin(admin.ModelAdmin):
    list_display = ["placeholder", "label", "category", "is_sensitive", "is_active"]
    list_filter = ["category", "is_sensitive", "is_active"]
    search_fields = ["code", "label", "description", "source_path"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(MessageQueue)
class MessageQueueAdmin(admin.ModelAdmin):
    list_display = [
        "recipient",
        "channel",
        "message_type",
        "status",
        "scheduled_at",
        "retry_count",
    ]
    list_filter = ["channel", "message_type", "status"]
    search_fields = ["recipient", "subject", "body"]
    readonly_fields = ["provider_response", "created_at", "updated_at"]


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = [
        "recipient",
        "channel",
        "message_type",
        "status",
        "sent_at",
        "provider",
    ]
    list_filter = ["channel", "message_type", "status", "provider"]
    search_fields = ["recipient", "subject", "body_snapshot", "error_message"]
    readonly_fields = ["body_snapshot", "created_at"]


admin.site.register(MessageProvider)
admin.site.register(MessagePreference)
admin.site.register(MessageEvent)
admin.site.register(MessageAttachment)
