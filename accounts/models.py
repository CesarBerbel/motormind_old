from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom user model using email as the unique authentication field.
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

    def __str__(self):
        return self.email
