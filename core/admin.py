from django.contrib import admin

from .models import CompanySettings


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    """
    Readable Django Admin registration for the single workshop settings record.
    """

    list_display = (
        "name",
        "document",
        "phone",
        "email",
        "city",
        "state",
        "is_configured",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "name",
                    "legal_name",
                    "document",
                    "state_registration",
                    "municipal_registration",
                    "is_configured",
                )
            },
        ),
        (
            "Contato",
            {
                "fields": (
                    "phone",
                    "whatsapp",
                    "email",
                    "website",
                )
            },
        ),
        (
            "Endereço",
            {
                "fields": (
                    "address_line",
                    "number",
                    "complement",
                    "neighborhood",
                    "city",
                    "state",
                    "zip_code",
                )
            },
        ),
        (
            "Operação",
            {
                "fields": (
                    "opening_hours",
                    "service_terms",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not CompanySettings.objects.exists()
