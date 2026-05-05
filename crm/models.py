from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import SoftDeleteModel
from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


class CustomerTag(SoftDeleteModel):
    name = models.CharField(max_length=80, unique=True, verbose_name="Nome")
    color = models.CharField(max_length=20, blank=True, verbose_name="Cor CSS")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Tag de cliente"
        verbose_name_plural = "Tags de cliente"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerInteraction(SoftDeleteModel):
    class InteractionType(models.TextChoices):
        CALL = "call", "Ligação"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        VISIT = "visit", "Visita"
        SERVICE_ORDER = "service_order", "Ordem de serviço"
        POST_SALE = "post_sale", "Pós-venda"
        PORTAL = "portal", "Portal do cliente"
        CAMPAIGN = "campaign", "Campanha"
        INTERNAL = "internal", "Interna"

    class Channel(models.TextChoices):
        PHONE = "phone", "Telefone"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        IN_PERSON = "in_person", "Presencial"
        SYSTEM = "system", "Sistema"
        PORTAL = "portal", "Portal"
        OTHER = "other", "Outro"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="crm_interactions",
        verbose_name="Cliente",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name="crm_interactions",
        blank=True,
        null=True,
        verbose_name="Veículo",
    )
    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.SET_NULL,
        related_name="crm_interactions",
        blank=True,
        null=True,
        verbose_name="Ordem de serviço",
    )
    interaction_type = models.CharField(
        max_length=30, choices=InteractionType.choices, verbose_name="Tipo"
    )
    channel = models.CharField(
        max_length=30,
        choices=Channel.choices,
        default=Channel.SYSTEM,
        verbose_name="Canal",
    )
    subject = models.CharField(max_length=150, verbose_name="Assunto")
    description = models.TextField(verbose_name="Descrição")
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="crm_interactions",
        blank=True,
        null=True,
        verbose_name="Responsável",
    )
    interaction_date = models.DateTimeField(
        default=timezone.now, verbose_name="Data da interação"
    )
    next_follow_up_date = models.DateField(
        blank=True, null=True, verbose_name="Próximo follow-up"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Interação de CRM"
        verbose_name_plural = "Interações de CRM"
        ordering = ["-interaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["customer", "-interaction_date"]),
            models.Index(fields=["service_order", "-interaction_date"]),
            models.Index(fields=["next_follow_up_date"]),
        ]

    def __str__(self):
        return f"{self.customer} - {self.subject}"


class CustomerOpportunity(SoftDeleteModel):
    class Status(models.TextChoices):
        OPEN = "open", "Aberta"
        WON = "won", "Ganha"
        LOST = "lost", "Perdida"
        CANCELED = "canceled", "Cancelada"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="crm_opportunities",
        verbose_name="Cliente",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name="crm_opportunities",
        blank=True,
        null=True,
        verbose_name="Veículo",
    )
    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.SET_NULL,
        related_name="crm_opportunities",
        blank=True,
        null=True,
        verbose_name="Ordem de serviço",
    )
    title = models.CharField(max_length=150, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")
    estimated_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Valor estimado",
    )
    probability = models.PositiveSmallIntegerField(
        default=50, verbose_name="Probabilidade (%)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Status",
    )
    expected_close_date = models.DateField(
        blank=True, null=True, verbose_name="Previsão de fechamento"
    )
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="crm_opportunities",
        blank=True,
        null=True,
        verbose_name="Responsável",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Oportunidade de CRM"
        verbose_name_plural = "Oportunidades de CRM"
        ordering = ["status", "expected_close_date", "-created_at"]

    def __str__(self):
        return self.title


class CustomerReminder(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        DONE = "done", "Concluído"
        CANCELED = "canceled", "Cancelado"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="crm_reminders",
        verbose_name="Cliente",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name="crm_reminders",
        blank=True,
        null=True,
        verbose_name="Veículo",
    )
    service_order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.SET_NULL,
        related_name="crm_reminders",
        blank=True,
        null=True,
        verbose_name="Ordem de serviço",
    )
    title = models.CharField(max_length=150, verbose_name="Título")
    notes = models.TextField(blank=True, verbose_name="Observações")
    due_date = models.DateField(verbose_name="Data de vencimento")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="crm_reminders",
        blank=True,
        null=True,
        verbose_name="Responsável",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Lembrete de CRM"
        verbose_name_plural = "Lembretes de CRM"
        ordering = ["status", "due_date", "customer__name"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return self.title


class Campaign(SoftDeleteModel):
    class CampaignType(models.TextChoices):
        POST_SALE = "post_sale", "Pós-venda"
        PREVENTIVE_MAINTENANCE = "preventive_maintenance", "Revisão preventiva"
        INACTIVE_CUSTOMERS = "inactive_customers", "Clientes inativos"
        PROMOTION = "promotion", "Promoção"
        BIRTHDAY = "birthday", "Aniversário"

    class Channel(models.TextChoices):
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        PHONE = "phone", "Telefone"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SCHEDULED = "scheduled", "Agendada"
        RUNNING = "running", "Em execução"
        FINISHED = "finished", "Finalizada"
        CANCELED = "canceled", "Cancelada"

    name = models.CharField(max_length=150, verbose_name="Nome")
    campaign_type = models.CharField(
        max_length=40, choices=CampaignType.choices, verbose_name="Tipo"
    )
    channel = models.CharField(
        max_length=20, choices=Channel.choices, verbose_name="Canal"
    )
    subject = models.CharField(max_length=150, verbose_name="Assunto")
    message = models.TextField(verbose_name="Mensagem")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Status",
    )
    scheduled_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Agendada para"
    )
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="Iniciada em")
    finished_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Finalizada em"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="crm_campaigns",
        blank=True,
        null=True,
        verbose_name="Criada por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Campanha de CRM"
        verbose_name_plural = "Campanhas de CRM"
        ordering = ["status", "-created_at"]

    def __str__(self):
        return self.name


class CampaignAudience(SoftDeleteModel):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="audience",
        verbose_name="Campanha",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="crm_campaign_audiences",
        verbose_name="Cliente",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Público da campanha"
        verbose_name_plural = "Público das campanhas"
        unique_together = ["campaign", "customer"]

    def __str__(self):
        return f"{self.campaign} - {self.customer}"
