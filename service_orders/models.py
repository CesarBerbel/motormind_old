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
        ordering = ["-created_at"]

    def __str__(self):
        return f"OS #{self.pk} - {self.customer.name}"

    @property
    def total_amount(self):
        """
        Calculate the total amount using Decimal fields.
        """
        total = self.labor_cost + self.parts_cost - self.discount

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
        ordering = ["-created_at"]

    def __str__(self):
        return f"OS #{self.service_order_id} - {self.field_name}"
