from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from customers.models import Customer, Vehicle


class ServiceOrder(models.Model):
    """
    Model that stores workshop service orders.
    """

    class Status(models.TextChoices):
        """
        Controlled status choices for service orders.
        """

        OPEN = "open", "Aberta"
        IN_PROGRESS = "in_progress", "Em execução"
        WAITING_PARTS = "waiting_parts", "Aguardando peças"
        WAITING_APPROVAL = "waiting_approval", "Aguardando aprovação"
        FINISHED = "finished", "Finalizada"
        CANCELED = "canceled", "Cancelada"

    class Priority(models.TextChoices):
        """
        Controlled priority choices for operational workflow.
        """

        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="Cliente",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="Veículo",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_service_orders",
        verbose_name="Criado por",
    )

    assigned_mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_service_orders",
        blank=True,
        null=True,
        verbose_name="Mecânico responsável",
    )

    title = models.CharField(
        max_length=150,
        verbose_name="Título",
    )

    description = models.TextField(
        verbose_name="Descrição do problema",
    )

    diagnosis = models.TextField(
        blank=True,
        null=True,
        verbose_name="Diagnóstico técnico",
    )

    solution = models.TextField(
        blank=True,
        null=True,
        verbose_name="Serviço executado",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Status",
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Prioridade",
    )

    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Valor da mão de obra",
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Valor das peças",
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Desconto",
    )

    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Previsão de entrega",
    )

    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Finalizada em",
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
        verbose_name = "Ordem de serviço"
        verbose_name_plural = "Ordens de serviço"
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"OS #{self.pk} - {self.customer.name}"

    @property
    def items_total(self):
        """
        Calculate total amount from service order items.
        """
        total = Decimal("0.00")

        for item in self.items.all():
            total += item.total

        return total

    @property
    def total_amount(self):
        """
        Calculate final total using legacy costs plus item totals.
        """
        total = self.labor_cost + self.parts_cost + self.items_total - self.discount

        if total < Decimal("0.00"):
            return Decimal("0.00")

        return total


class ServiceOrderHistory(models.Model):
    """
    Model that stores audit history for service order changes.
    """

    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Ordem de serviço",
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="service_order_changes",
        verbose_name="Alterado por",
    )

    field_name = models.CharField(
        max_length=100,
        verbose_name="Campo alterado",
    )

    old_value = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor antigo",
    )

    new_value = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor novo",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        verbose_name = "Histórico da ordem de serviço"
        verbose_name_plural = "Históricos das ordens de serviço"
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"OS #{self.service_order_id} - {self.field_name}"


class ServiceOrderItem(models.Model):
    """
    Model that stores parts and services linked to a service order.
    """

    class ItemType(models.TextChoices):
        """
        Controlled item types.
        """

        SERVICE = "service", "Serviço"
        PART = "part", "Peça"

    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Ordem de serviço",
    )

    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        verbose_name="Tipo",
    )

    description = models.CharField(
        max_length=255,
        verbose_name="Descrição",
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
        verbose_name="Quantidade",
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Preço unitário",
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
        verbose_name = "Item da ordem de serviço"
        verbose_name_plural = "Itens da ordem de serviço"
        ordering = [
            "created_at",
        ]

    def __str__(self):
        return self.description

    @property
    def total(self):
        """
        Calculate item total using Decimal values.
        """
        return self.quantity * self.unit_price


class ServiceOrderNote(models.Model):
    """
    Model that stores internal notes linked to service orders.
    """

    class NoteType(models.TextChoices):
        """
        Controlled note types.
        """

        INTERNAL = "internal", "Interna"
        CUSTOMER = "customer", "Cliente"
        TECHNICAL = "technical", "Técnica"
        URGENT = "urgent", "Urgente"

    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="Ordem de serviço",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="service_order_notes",
        verbose_name="Criado por",
    )

    note_type = models.CharField(
        max_length=20,
        choices=NoteType.choices,
        default=NoteType.INTERNAL,
        verbose_name="Tipo",
    )

    text = models.TextField(
        verbose_name="Observação",
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
        verbose_name = "Nota interna da ordem de serviço"
        verbose_name_plural = "Notas internas das ordens de serviço"
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"OS #{self.service_order_id} - {self.get_note_type_display()}"
