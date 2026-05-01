from django.core.validators import RegexValidator
from django.db import models

from core.validators import only_digits, validate_document


class Customer(models.Model):
    """
    Model that stores workshop customer information.
    """

    name = models.CharField(
        max_length=150,
        verbose_name="Nome",
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="Telefone",
        validators=[
            RegexValidator(
                regex=r"^[0-9+\-\s()]+$",
                message="Informe um telefone válido.",
            )
        ],
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email",
    )

    document = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Documento",
        help_text="CPF, CNPJ, NIF ou outro documento fiscal.",
        validators=[validate_document],
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Endereço",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
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

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.document = only_digits(self.document)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    """
    Model that stores vehicles linked to customers.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="Cliente",
    )

    plate = models.CharField(
        max_length=20,
        verbose_name="Matrícula/Placa",
    )

    brand = models.CharField(
        max_length=80,
        verbose_name="Marca",
    )

    model = models.CharField(
        max_length=80,
        verbose_name="Modelo",
    )

    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Ano",
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Cor",
    )

    chassis_number = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name="Número do chassi",
    )

    mileage = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Quilometragem",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
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

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ["plate"]
        constraints = [
            models.UniqueConstraint(
                fields=["plate"],
                name="unique_vehicle_plate",
            )
        ]

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"
