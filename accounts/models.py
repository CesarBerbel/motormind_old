from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom user model using email as the unique authentication field.

    User classification rules:
    - a superuser cannot be a customer;
    - a superuser cannot be an employee;
    - a customer cannot be an employee at the same time.
    """

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        error_messages={
            "unique": "Já existe um usuário cadastrado com este email.",
        },
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nome",
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Sobrenome",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    is_customer = models.BooleanField(
        default=False,
        verbose_name="Cliente",
        help_text="Marque quando este usuário representa um cliente no portal.",
    )

    is_employee = models.BooleanField(
        default=True,
        verbose_name="Funcionário",
        help_text="Marque quando este usuário representa um funcionário da oficina.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["email"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(is_superuser=False)
                    | (models.Q(is_customer=False) & models.Q(is_employee=False))
                ),
                name="accounts_superuser_not_customer_or_employee",
            ),
            models.CheckConstraint(
                condition=models.Q(is_customer=False) | models.Q(is_employee=False),
                name="accounts_user_not_customer_and_employee",
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def user_type_label(self):
        if self.is_superuser:
            return "Superuser"
        if self.is_customer:
            return "Cliente"
        if self.is_employee:
            return "Funcionário"
        return "Sem tipo definido"

    def clean(self):
        super().clean()

        errors = {}

        if self.is_superuser and (self.is_customer or self.is_employee):
            message = "Superuser não pode ser cliente nem funcionário."
            errors["is_superuser"] = message
            if self.is_customer:
                errors["is_customer"] = message
            if self.is_employee:
                errors["is_employee"] = message

        if self.is_customer and self.is_employee:
            message = "Um usuário não pode ser cliente e funcionário ao mesmo tempo."
            errors["is_customer"] = message
            errors["is_employee"] = message

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
