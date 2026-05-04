from django.contrib import admin

from .models import (
    Campaign,
    CampaignAudience,
    CustomerInteraction,
    CustomerOpportunity,
    CustomerReminder,
    CustomerTag,
)


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    search_fields = ["name"]


@admin.register(CustomerInteraction)
class CustomerInteractionAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "interaction_type",
        "channel",
        "subject",
        "responsible_user",
        "interaction_date",
    ]
    list_filter = ["interaction_type", "channel", "interaction_date"]
    search_fields = ["customer__name", "subject", "description"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


@admin.register(CustomerOpportunity)
class CustomerOpportunityAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "customer",
        "status",
        "estimated_value",
        "probability",
        "expected_close_date",
    ]
    list_filter = ["status", "expected_close_date"]
    search_fields = ["title", "customer__name"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


@admin.register(CustomerReminder)
class CustomerReminderAdmin(admin.ModelAdmin):
    list_display = ["title", "customer", "due_date", "status", "responsible_user"]
    list_filter = ["status", "due_date"]
    search_fields = ["title", "customer__name"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


class CampaignAudienceInline(admin.TabularInline):
    model = CampaignAudience
    extra = 0
    autocomplete_fields = ["customer"]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "campaign_type",
        "channel",
        "status",
        "scheduled_at",
        "created_by",
    ]
    list_filter = ["campaign_type", "channel", "status"]
    search_fields = ["name", "subject", "message"]
    inlines = [CampaignAudienceInline]
