from django.contrib import admin

from .models import AIPromptTemplate, AIRequest, AIResponse, AIReview, AIUsageLog


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "use_case", "version", "is_active", "updated_at")
    list_filter = ("use_case", "is_active")
    search_fields = ("name", "code", "system_prompt", "user_prompt_template")


class AIResponseInline(admin.StackedInline):
    model = AIResponse
    extra = 0
    readonly_fields = (
        "output_text",
        "model_name",
        "tokens_input",
        "tokens_output",
        "latency_ms",
        "raw_response",
        "created_at",
    )
    can_delete = False


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "use_case", "status", "prompt_template", "created_at")
    list_filter = ("use_case", "status", "created_at")
    search_fields = ("rendered_prompt", "error_message", "user__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AIResponseInline]


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "model_name",
        "tokens_input",
        "tokens_output",
        "latency_ms",
        "created_at",
    )
    search_fields = ("output_text", "model_name")
    readonly_fields = ("created_at",)


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "feature", "use_case", "status", "created_at")
    list_filter = ("use_case", "status", "created_at")
    search_fields = ("feature", "user__email")
    readonly_fields = ("created_at",)


@admin.register(AIReview)
class AIReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "response", "reviewed_by", "status", "reviewed_at")
    list_filter = ("status", "reviewed_at")
    search_fields = ("notes", "edited_output_text", "reviewed_by__email")
