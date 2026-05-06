from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone

from core.models import SoftDeleteModel
from customers.models import Customer, Vehicle


class ServiceOrder(SoftDeleteModel):
    """
    Model that stores workshop service orders.
    """

    class Status(models.TextChoices):
        """
        Controlled status choices for service orders.
        """

        OPEN = "open", "Aberta"
        IN_DIAGNOSIS = "in_diagnosis", "Em diagnóstico"
        WAITING_APPROVAL = "waiting_approval", "Aguardando aprovação"
        APPROVED = "approved", "Aprovada"
        IN_PROGRESS = "in_progress", "Em execução"
        WAITING_PARTS = "waiting_parts", "Aguardando peças"
        FINISHED = "finished", "Finalizada"
        BILLED = "billed", "Faturada"
        PAID = "paid", "Paga"
        CANCELED = "canceled", "Cancelada"

    class Priority(models.TextChoices):
        """
        Controlled priority choices for operational workflow.
        """

        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"

    class OrderType(models.TextChoices):
        """
        Controlled operational type choices for service orders.
        """

        NORMAL = "normal", "Normal"
        WARRANTY = "warranty", "Garantia"
        RETURN = "return", "Retorno"

    number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        editable=False,
        verbose_name="Número da OS",
    )

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

    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.NORMAL,
        verbose_name="Tipo da OS",
    )

    warranty_origin_order = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="warranty_orders",
        blank=True,
        null=True,
        verbose_name="OS original da garantia/retorno",
    )

    warranty_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo da garantia/retorno",
    )

    warranty_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_warranty_service_orders",
        blank=True,
        null=True,
        verbose_name="Garantia aprovada por",
    )

    warranty_approved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Garantia aprovada em",
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
        return f"OS {self.display_number} - {self.customer.name}"

    @property
    def display_number(self):
        """
        Return the public service order number.
        """
        return self.number or f"#{self.pk}"

    @property
    def is_budget_approved(self):
        """
        Check if the service order already has a formal budget approval.
        """
        return hasattr(self, "approval")

    def save(self, *args, **kwargs):
        """
        Save the service order and create a public sequential number when needed.
        """
        needs_number = not self.number

        super().save(*args, **kwargs)

        if needs_number and self.pk:
            year = (
                self.created_at.year if self.created_at else timezone.localdate().year
            )
            self.number = f"OS-{year}-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(number=self.number)

    @property
    def allowed_next_status_choices(self):
        """
        Return UI-safe status choices according to the service order state machine.
        """
        from service_orders.services import get_allowed_next_status_choices

        return get_allowed_next_status_choices(self)

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
    def services_total(self):
        return self.items.filter(item_type=ServiceOrderItem.ItemType.SERVICE).aggregate(
            total=Sum(F("quantity") * F("unit_price"))
        ).get("total") or Decimal("0.00")

    @property
    def parts_total(self):
        return self.inventory_parts.aggregate(
            total=Sum(F("quantity") * F("unit_price") - F("discount"))
        ).get("total") or Decimal("0.00")

    @property
    def total_amount(self):
        """
        Return the net total from the single financial summary contract.
        """
        from service_orders.selectors import get_service_order_financial_summary

        return get_service_order_financial_summary(self)["net_total"]


class ServiceOrderHistory(SoftDeleteModel):
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


class ServiceOrderItem(SoftDeleteModel):
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


class ServiceOrderNote(SoftDeleteModel):
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


class ServiceOrderTimeEntry(SoftDeleteModel):
    """
    Model that stores mechanic time tracking entries for service orders.
    """

    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name="time_entries",
        verbose_name="Ordem de serviço",
    )

    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="service_order_time_entries",
        verbose_name="Mecânico",
    )

    started_at = models.DateTimeField(
        verbose_name="Iniciado em",
    )

    ended_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Encerrado em",
    )

    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observação",
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
        verbose_name = "Apontamento de tempo da OS"
        verbose_name_plural = "Apontamentos de tempo das OS"
        ordering = ["-started_at"]

    def __str__(self):
        return f"OS #{self.service_order_id} - {self.mechanic.email}"

    @property
    def is_open(self):
        """
        Check if time entry is still running.
        """
        return self.ended_at is None

    @property
    def duration(self):
        """
        Return duration between start and end.
        """
        end = self.ended_at or timezone.now()

        return end - self.started_at


class ServiceOrderApproval(SoftDeleteModel):
    """
    Model that stores the formal approved budget snapshot for a service order.
    """

    class Channel(models.TextChoices):
        """
        Controlled approval channels.
        """

        IN_PERSON = "in_person", "Presencial"
        PHONE = "phone", "Telefone"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        PORTAL = "portal", "Portal do cliente"
        OTHER = "other", "Outro"

    service_order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.PROTECT,
        related_name="approval",
        verbose_name="Ordem de serviço",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_service_orders",
        verbose_name="Aprovado por",
    )

    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        verbose_name="Canal de aprovação",
    )

    customer_name_snapshot = models.CharField(
        max_length=255,
        verbose_name="Nome do cliente no momento da aprovação",
    )

    vehicle_snapshot = models.CharField(
        max_length=255,
        verbose_name="Veículo no momento da aprovação",
    )

    gross_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total bruto aprovado",
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Desconto aprovado",
    )

    net_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total líquido aprovado",
    )

    financial_summary_snapshot = models.JSONField(
        default=dict,
        verbose_name="Snapshot financeiro aprovado",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Observações da aprovação",
    )

    approved_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Aprovado em",
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
        verbose_name = "Aprovação de orçamento da OS"
        verbose_name_plural = "Aprovações de orçamento das OS"
        ordering = ["-approved_at"]

    def __str__(self):
        return f"Aprovação {self.service_order.display_number}"
