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

    zip_code = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="CEP",
        help_text="Informe o CEP para preenchimento automático do endereço.",
        validators=[
            RegexValidator(
                regex=r"^\d{5}-?\d{3}$",
                message="Informe um CEP válido no formato 00000-000.",
            )
        ],
    )

    street = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Logradouro",
    )

    number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número",
    )

    complement = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Complemento",
    )

    neighborhood = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Bairro",
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cidade",
    )

    state = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name="UF",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Endereço completo",
        help_text="Campo legado preenchido automaticamente a partir dos campos detalhados.",
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
        self.zip_code = self._format_zip_code(self.zip_code)
        self.state = self.state.upper() if self.state else self.state
        self.address = self.get_full_address()
        super().save(*args, **kwargs)

    @staticmethod
    def _format_zip_code(zip_code):
        if not zip_code:
            return zip_code

        digits = only_digits(zip_code)
        if len(digits) == 8:
            return f"{digits[:5]}-{digits[5:]}"
        return zip_code

    def get_full_address(self):
        parts = []

        if self.street:
            street_line = self.street
            if self.number:
                street_line = f"{street_line}, {self.number}"
            parts.append(street_line)

        if self.complement:
            parts.append(self.complement)

        if self.neighborhood:
            parts.append(self.neighborhood)

        city_state = " / ".join(part for part in [self.city, self.state] if part)
        if city_state:
            parts.append(city_state)

        if self.zip_code:
            parts.append(f"CEP {self.zip_code}")

        return " - ".join(parts)

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
