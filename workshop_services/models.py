from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum

from core.models import SoftDeleteModel


class WorkshopServiceCategory(SoftDeleteModel):
    """
    Independent category catalog for workshop services.
    """

    name = models.CharField(max_length=80, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Categoria de serviço"
        verbose_name_plural = "Categorias de serviços"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkshopService(SoftDeleteModel):
    """
    Catalog item for services sold by the workshop.
    """

    name = models.CharField(max_length=150, verbose_name="Nome do serviço")
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código interno",
    )
    category = models.ForeignKey(
        WorkshopServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        blank=True,
        null=True,
        verbose_name="Categoria",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
    )
    default_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço padrão",
    )
    estimated_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Tempo estimado em minutos",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkshopServicePart(SoftDeleteModel):
    """
    Default inventory part required by a catalog service.
    These parts are copied to the service order when the service is added.
    """

    service = models.ForeignKey(
        WorkshopService,
        on_delete=models.CASCADE,
        related_name="default_parts",
        verbose_name="Serviço",
    )
    part = models.ForeignKey(
        "inventory.Part",
        on_delete=models.PROTECT,
        related_name="workshop_service_templates",
        verbose_name="Peça",
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Quantidade padrão",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço unitário",
        help_text="Deixe vazio para usar o preço de venda atual da peça.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Peça padrão do serviço"
        verbose_name_plural = "Peças padrão dos serviços"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "part"],
                name="unique_default_part_per_workshop_service",
            )
        ]

    def __str__(self):
        return f"{self.service.name} - {self.part.name}"

    @property
    def effective_unit_price(self):
        if self.unit_price is not None:
            return self.unit_price
        return self.part.sale_price

    @property
    def total(self):
        return self.quantity * self.effective_unit_price

    def clean(self):
        super().clean()

        if self.part_id and not self.part.is_active:
            raise ValidationError({"part": "Não é possível vincular uma peça inativa ao serviço."})


class ServiceCombo(SoftDeleteModel):
    """
    Commercial package composed of multiple catalog services.
    """

    name = models.CharField(max_length=150, verbose_name="Nome do combo")
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código interno",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Desconto do combo",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Combo de serviços"
        verbose_name_plural = "Combos de serviços"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def gross_total(self):
        total = self.items.aggregate(total=Sum(F("quantity") * F("unit_price")))[
            "total"
        ]
        return total or Decimal("0.00")

    @property
    def total(self):
        total = self.gross_total - self.discount_amount
        if total < Decimal("0.00"):
            return Decimal("0.00")
        return total

    def clean(self):
        super().clean()
        if self.discount_amount > self.gross_total and self.pk:
            raise ValidationError(
                {
                    "discount_amount": "O desconto não pode ser maior que o subtotal do combo."
                }
            )


class ServiceComboItem(SoftDeleteModel):
    """
    Service line inside a combo.
    """

    combo = models.ForeignKey(
        ServiceCombo,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Combo",
    )
    service = models.ForeignKey(
        WorkshopService,
        on_delete=models.PROTECT,
        related_name="combo_items",
        verbose_name="Serviço",
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Quantidade",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço unitário no combo",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Item do combo"
        verbose_name_plural = "Itens do combo"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["combo", "service"],
                name="unique_service_per_combo",
            )
        ]

    def __str__(self):
        return f"{self.combo.name} - {self.service.name}"

    @property
    def total(self):
        return self.quantity * self.unit_price

    def clean(self):
        super().clean()
        if self.service_id and not self.service.is_active:
            raise ValidationError(
                {"service": "Não é possível adicionar serviço inativo ao combo."}
            )
