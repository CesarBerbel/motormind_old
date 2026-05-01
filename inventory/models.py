from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Part(models.Model):
    """
    Model that stores parts available in workshop inventory.
    """

    name = models.CharField(
        max_length=150,
        verbose_name="Nome da peça",
    )

    internal_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código interno",
    )

    barcode = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name="Código de barras",
    )

    brand = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name="Marca",
    )

    category = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name="Categoria",
    )

    unit = models.CharField(
        max_length=20,
        default="un",
        verbose_name="Unidade de medida",
    )

    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Preço de custo",
    )

    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Preço de venda",
    )

    current_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Estoque atual",
    )

    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Estoque mínimo",
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Localização no estoque",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criada em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizada em",
    )

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = [
            "name",
        ]

    def __str__(self):
        return f"{self.internal_code} - {self.name}"

    @property
    def is_low_stock(self):
        """
        Check if current stock is less than or equal to minimum stock.
        """
        return self.current_stock <= self.minimum_stock

    @property
    def stock_status_label(self):
        """
        Return readable stock status.
        """
        if self.is_low_stock:
            return "Estoque baixo"

        return "Estoque normal"


class StockMovement(models.Model):
    """
    Model that stores inventory movement history.
    """

    class MovementType(models.TextChoices):
        """
        Controlled movement types.
        """

        IN = "in", "Entrada"
        OUT = "out", "Saída"
        ADJUST = "adjust", "Ajuste"
        RETURN = "return", "Devolução"
        LOSS = "loss", "Perda"
        RESERVE = "reserve", "Reserva"
        RELEASE = "release", "Liberação de reserva"

    part = models.ForeignKey(
        Part,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Peça",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name="Tipo de movimentação",
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
        verbose_name="Quantidade",
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Custo unitário",
    )

    unit_sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Preço de venda unitário",
    )

    reason = models.TextField(
        verbose_name="Motivo",
    )

    service_order = models.ForeignKey(
        "service_orders.ServiceOrder",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        blank=True,
        null=True,
        verbose_name="Ordem de serviço relacionada",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criada em",
    )

    class Meta:
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.part.name}"

    def clean(self):
        """
        Validate stock movement business rules.
        """
        super().clean()

        if self.quantity is None:
            return

        if self.quantity <= Decimal("0.00"):
            raise ValidationError(
                {
                    "quantity": "A quantidade deve ser maior que zero.",
                }
            )

        reducing_types = [
            self.MovementType.OUT,
            self.MovementType.LOSS,
            self.MovementType.RESERVE,
        ]

        if self.movement_type in reducing_types and self.part_id:
            if self.quantity > self.part.current_stock:
                raise ValidationError(
                    {
                        "quantity": "Estoque insuficiente para esta movimentação.",
                    }
                )
