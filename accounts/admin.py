from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for custom user model.

    The Django Admin intentionally does not expose user-type flags or the
    superuser flag in the create/edit form. Superuser accounts must be created
    through the createsuperuser management command. Internal staff accounts can
    be maintained here as employees, while customer users belong to the
    customer/portal flow.
    """

    model = CustomUser

    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_type_label",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
        "is_customer",
        "is_employee",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("email",)

    fieldsets = (
        (
            "Dados de acesso",
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Dados pessoais",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Permissões de funcionário",
            {
                "fields": (
                    "is_active",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Datas importantes",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    add_fieldsets = (
        (
            "Criar novo funcionário",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_staff = False
            obj.is_superuser = False
            obj.is_customer = False
            obj.is_employee = True
        super().save_model(request, obj, form, change)
