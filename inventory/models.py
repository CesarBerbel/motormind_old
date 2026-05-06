from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import SoftDeleteModel


class PartBrand(SoftDeleteModel):
    """
    Stores normalized automotive part brands.
    """

    name = models.CharField(max_length=80, unique=True, verbose_name="Nome da marca")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Marca de peça"
        verbose_name_plural = "Marcas de peças"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PartCategory(SoftDeleteModel):
    """
    Stores normalized automotive part categories.
    """

    name = models.CharField(
        max_length=80, unique=True, verbose_name="Nome da categoria"
    )
    description = models.TextField(blank=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Categoria de peça"
        verbose_name_plural = "Categorias de peças"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Part(SoftDeleteModel):
    """
    Model that stores parts available in workshop inventory.
    """

    name = models.CharField(max_length=150, verbose_name="Nome da peça")
    internal_code = models.CharField(
        max_length=50, unique=True, verbose_name="Código interno"
    )
    barcode = models.CharField(
        max_length=80, blank=True, null=True, verbose_name="Código de barras"
    )
    brand = models.ForeignKey(
        PartBrand,
        on_delete=models.PROTECT,
        related_name="parts",
        blank=True,
        null=True,
        verbose_name="Marca",
    )
    category = models.ForeignKey(
        PartCategory,
        on_delete=models.PROTECT,
        related_name="parts",
        blank=True,
        null=True,
        verbose_name="Categoria",
    )
    unit = models.CharField(
        max_length=20, default="un", verbose_name="Unidade de medida"
    )

    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço de custo",
    )

    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço de venda",
    )

    current_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Estoque atual",
    )

    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Estoque mínimo",
    )

    location = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Localização"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = ["name"]

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


class StockMovement(SoftDeleteModel):
    """
    Model that stores inventory movement history.
    """

    class MovementType(models.TextChoices):
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
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Quantidade",
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Custo unitário",
    )

    unit_sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço de venda unitário",
    )

    reason = models.TextField(verbose_name="Motivo")

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

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")

    class Meta:
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ["-created_at"]

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
            raise ValidationError({"quantity": "A quantidade deve ser maior que zero."})

        reducing_types = [
            self.MovementType.OUT,
            self.MovementType.LOSS,
            self.MovementType.RESERVE,
        ]

        if self.movement_type in reducing_types and self.part_id:
            if self.quantity > self.part.current_stock:
                raise ValidationError(
                    {"quantity": "Estoque insuficiente para esta movimentação."}
                )


class ServiceOrderPart(SoftDeleteModel):
    """
    Model that links inventory parts to service orders.
    """

    class Status(models.TextChoices):
        RESERVED = "reserved", "Reservada"
        WAITING_PURCHASE = "waiting_purchase", "Aguardando compra"
        USED = "used", "Usada"
        RETURNED = "returned", "Devolvida"
        CANCELED = "canceled", "Cancelada"

    service_order = models.ForeignKey(
        "service_orders.ServiceOrder",
        on_delete=models.CASCADE,
        related_name="inventory_parts",
        verbose_name="Ordem de serviço",
    )

    service_order_item = models.ForeignKey(
        "service_orders.ServiceOrderItem",
        on_delete=models.PROTECT,
        related_name="inventory_parts",
        blank=True,
        null=True,
        verbose_name="Serviço da OS",
        help_text="Serviço específico da OS que originou esta peça.",
    )

    part = models.ForeignKey(
        Part,
        on_delete=models.PROTECT,
        related_name="service_order_parts",
        verbose_name="Peça",
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Quantidade solicitada",
    )

    reserved_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Quantidade reservada em estoque",
        help_text="Quantidade efetivamente baixada/reservada do estoque. A diferença abre pedido de compra.",
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço unitário",
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Desconto",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RESERVED,
        verbose_name="Status",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_service_order_parts",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Peça da ordem de serviço"
        verbose_name_plural = "Peças das ordens de serviço"
        ordering = ["created_at"]

    def __str__(self):
        return f"OS #{self.service_order_id} - {self.part.name}"

    @property
    def subtotal(self):
        """
        Return subtotal safely, even when admin form is creating a new object.
        """
        quantity = self.quantity or Decimal("0.00")
        unit_price = self.unit_price or Decimal("0.00")

        return quantity * unit_price

    @property
    def total(self):
        """
        Calculate total after discount.
        """
        total = self.subtotal - self.discount

        if total < Decimal("0.00"):
            return Decimal("0.00")

        return total

    def clean(self):
        """
        Validate service order part.
        """
        super().clean()

        if (
            self.service_order_item_id
            and self.service_order_item.service_order_id != self.service_order_id
        ):
            raise ValidationError(
                {"service_order_item": "O serviço vinculado deve pertencer à mesma OS."}
            )

        if self.part_id and not self.part.is_active:
            raise ValidationError({"part": "Não é possível usar uma peça inativa."})

        if self.reserved_quantity > self.quantity:
            raise ValidationError(
                {
                    "reserved_quantity": (
                        "A quantidade reservada não pode ser maior que a "
                        "quantidade solicitada."
                    )
                }
            )

        if self.discount > self.subtotal:
            raise ValidationError(
                {"discount": "O desconto não pode ser maior que o subtotal."}
            )


class PurchaseOrder(SoftDeleteModel):
    """
    Pedido de compra aberto automaticamente quando uma OS solicita mais peças
    do que o saldo disponível em estoque.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Aberto"
        ORDERED = "ordered", "Compra solicitada"
        RECEIVED = "received", "Recebido"
        CANCELED = "canceled", "Cancelado"

    part = models.ForeignKey(
        Part,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        verbose_name="Peça",
    )
    service_order = models.ForeignKey(
        "service_orders.ServiceOrder",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        verbose_name="Ordem de serviço",
    )
    service_order_part = models.ForeignKey(
        ServiceOrderPart,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        blank=True,
        null=True,
        verbose_name="Peça da OS",
    )
    requested_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Quantidade a comprar",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Status",
    )
    reason = models.TextField(verbose_name="Motivo")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Pedido de compra"
        verbose_name_plural = "Pedidos de compra"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Compra {self.part.name} - OS #{self.service_order_id}"

    def clean(self):
        super().clean()

        if self.requested_quantity is not None and self.requested_quantity <= Decimal(
            "0.00"
        ):
            raise ValidationError(
                {
                    "requested_quantity": "A quantidade a comprar deve ser maior que zero."
                }
            )
