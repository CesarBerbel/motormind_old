from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum

from core.models import SoftDeleteModel


class WorkshopServiceCategory(SoftDeleteModel):
    """
    Independent hierarchical category catalog for workshop services.
    """

    name = models.CharField(max_length=80, unique=True, verbose_name="Nome")
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        blank=True,
        null=True,
        verbose_name="Categoria pai",
    )
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Categoria de serviço"
        verbose_name_plural = "Categorias de serviços"
        ordering = ["parent__name", "name"]

    def __str__(self):
        if self.parent_id:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        super().clean()
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "A categoria não pode ser pai dela mesma."})


class WorkshopService(SoftDeleteModel):
    """
    Catalog item for services sold by the workshop.
    """

    name = models.CharField(max_length=150, verbose_name="Nome do serviço")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código interno")
    category = models.ForeignKey(
        WorkshopServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        blank=True,
        null=True,
        verbose_name="Categoria",
    )
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    default_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Preço padrão",
    )
    estimated_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Tempo estimado em minutos",
        help_text="Tempo operacional padrão usado em agenda, previsão e produtividade.",
    )
    current_version = models.PositiveIntegerField(default=1, verbose_name="Versão atual")
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


class WorkshopServiceVersion(models.Model):
    """
    Immutable snapshot of the catalog service at a relevant change point.
    OS items store the version number in their description/snapshots by service execution.
    """

    service = models.ForeignKey(
        WorkshopService,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name="Serviço",
    )
    version_number = models.PositiveIntegerField(verbose_name="Número da versão")
    code_snapshot = models.CharField(max_length=50, verbose_name="Código")
    name_snapshot = models.CharField(max_length=150, verbose_name="Nome")
    category_snapshot = models.CharField(max_length=160, blank=True, verbose_name="Categoria")
    description_snapshot = models.TextField(blank=True, verbose_name="Descrição")
    default_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço padrão")
    estimated_minutes_snapshot = models.PositiveIntegerField(default=0, verbose_name="Tempo estimado")
    parts_snapshot = models.JSONField(default=list, blank=True, verbose_name="Peças da versão")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_workshop_service_versions",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")

    class Meta:
        verbose_name = "Versão de serviço"
        verbose_name_plural = "Versões de serviços"
        ordering = ["service", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "version_number"],
                name="unique_version_per_workshop_service",
            )
        ]

    def __str__(self):
        return f"{self.service} v{self.version_number}"


class ServiceCombo(SoftDeleteModel):
    """
    Commercial package composed of multiple catalog services.
    """

    name = models.CharField(max_length=150, verbose_name="Nome do combo")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código interno")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
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
        total = self.items.aggregate(total=Sum(F("quantity") * F("unit_price")))["total"]
        return total or Decimal("0.00")

    @property
    def estimated_minutes(self):
        return sum((item.estimated_minutes_total for item in self.items.select_related("service")), 0)

    @property
    def total(self):
        total = self.gross_total - self.discount_amount
        if total < Decimal("0.00"):
            return Decimal("0.00")
        return total

    def clean(self):
        super().clean()
        if self.discount_amount > self.gross_total and self.pk:
            raise ValidationError({"discount_amount": "O desconto não pode ser maior que o subtotal do combo."})


class ServiceComboItem(SoftDeleteModel):
    """
    Service line inside a combo.
    """

    combo = models.ForeignKey(ServiceCombo, on_delete=models.CASCADE, related_name="items", verbose_name="Combo")
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
        constraints = [models.UniqueConstraint(fields=["combo", "service"], name="unique_service_per_combo")]

    def __str__(self):
        return f"{self.combo.name} - {self.service.name}"

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def estimated_minutes_total(self):
        return int(self.quantity * self.service.estimated_minutes)

    def clean(self):
        super().clean()
        if self.service_id and not self.service.is_active:
            raise ValidationError({"service": "Não é possível adicionar serviço inativo ao combo."})


class WorkshopCatalogAuditLog(models.Model):
    """
    Audit trail for service catalog and combo changes.
    """

    class Action(models.TextChoices):
        SERVICE_CREATED = "service_created", "Serviço criado"
        SERVICE_UPDATED = "service_updated", "Serviço atualizado"
        SERVICE_PARTS_UPDATED = "service_parts_updated", "Peças do serviço atualizadas"
        COMBO_CREATED = "combo_created", "Combo criado"
        COMBO_UPDATED = "combo_updated", "Combo atualizado"
        COMBO_ITEMS_UPDATED = "combo_items_updated", "Serviços do combo atualizados"
        CATEGORY_CREATED = "category_created", "Categoria criada"
        CATEGORY_UPDATED = "category_updated", "Categoria atualizada"

    action = models.CharField(max_length=40, choices=Action.choices, verbose_name="Ação")
    service = models.ForeignKey(
        WorkshopService,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="catalog_audit_logs",
        verbose_name="Serviço",
    )
    combo = models.ForeignKey(
        ServiceCombo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="catalog_audit_logs",
        verbose_name="Combo",
    )
    category = models.ForeignKey(
        WorkshopServiceCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="catalog_audit_logs",
        verbose_name="Categoria",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="workshop_catalog_audit_logs",
        verbose_name="Alterado por",
    )
    old_data = models.JSONField(default=dict, blank=True, verbose_name="Dados anteriores")
    new_data = models.JSONField(default=dict, blank=True, verbose_name="Dados novos")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Auditoria do catálogo"
        verbose_name_plural = "Auditorias do catálogo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} em {self.created_at:%d/%m/%Y %H:%M}"
