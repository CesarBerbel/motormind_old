from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from customers.models import Customer


class MessageChannel(models.TextChoices):
    EMAIL = "email", "E-mail"
    WHATSAPP = "whatsapp", "WhatsApp"


class MessageType(models.TextChoices):
    TRANSACTIONAL = "transactional", "Transacional"
    MARKETING = "marketing", "Comercial"
    RELATIONSHIP = "relationship", "Relacionamento"
    SYSTEM = "system", "Sistema"
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automática"


class MessageStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    PENDING = "pending", "Pendente"
    PROCESSING = "processing", "Processando"
    SENT = "sent", "Enviada"
    FAILED = "failed", "Falhou"
    CANCELED = "canceled", "Cancelada"


class MessageProvider(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    channel = models.CharField(
        max_length=20, choices=MessageChannel.choices, verbose_name="Canal"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    settings = models.JSONField(default=dict, blank=True, verbose_name="Configurações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Provedor de mensagem"
        verbose_name_plural = "Provedores de mensagem"
        ordering = ["channel", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


class MessageTemplate(models.Model):
    name = models.CharField(max_length=120, verbose_name="Nome")
    code = models.SlugField(max_length=80, unique=True, verbose_name="Código")
    channel = models.CharField(
        max_length=20, choices=MessageChannel.choices, verbose_name="Canal"
    )
    message_type = models.CharField(
        max_length=30, choices=MessageType.choices, verbose_name="Tipo"
    )
    subject = models.CharField(max_length=180, blank=True, verbose_name="Assunto")
    body = models.TextField(verbose_name="Corpo")
    available_variables = models.JSONField(
        default=list, blank=True, verbose_name="Variáveis disponíveis"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Template de mensagem"
        verbose_name_plural = "Templates de mensagem"
        ordering = ["channel", "name"]
        indexes = [models.Index(fields=["code", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


class MessagePreference(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="message_preference",
        verbose_name="Cliente",
    )
    accepts_email_transactional = models.BooleanField(
        default=True, verbose_name="Aceita e-mail transacional"
    )
    accepts_whatsapp_transactional = models.BooleanField(
        default=True, verbose_name="Aceita WhatsApp transacional"
    )
    accepts_email_marketing = models.BooleanField(
        default=False, verbose_name="Aceita e-mail comercial"
    )
    accepts_whatsapp_marketing = models.BooleanField(
        default=False, verbose_name="Aceita WhatsApp comercial"
    )
    preferred_channel = models.CharField(
        max_length=20,
        choices=MessageChannel.choices,
        default=MessageChannel.WHATSAPP,
        verbose_name="Canal preferido",
    )
    consent_source = models.CharField(
        max_length=120, blank=True, verbose_name="Origem do consentimento"
    )
    consent_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Data do consentimento"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Preferência de mensagem"
        verbose_name_plural = "Preferências de mensagem"

    def __str__(self):
        return f"Preferências de {self.customer}"


class MessageQueue(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="message_queue",
        blank=True,
        null=True,
        verbose_name="Cliente",
    )
    channel = models.CharField(
        max_length=20, choices=MessageChannel.choices, verbose_name="Canal"
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        related_name="queued_messages",
        blank=True,
        null=True,
        verbose_name="Template",
    )
    message_type = models.CharField(
        max_length=30, choices=MessageType.choices, verbose_name="Tipo"
    )
    recipient = models.CharField(max_length=180, verbose_name="Destinatário")
    subject = models.CharField(max_length=180, blank=True, verbose_name="Assunto")
    body = models.TextField(verbose_name="Corpo")
    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
        verbose_name="Status",
    )
    scheduled_at = models.DateTimeField(
        default=timezone.now, verbose_name="Agendada para"
    )
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Enviada em")
    failed_at = models.DateTimeField(blank=True, null=True, verbose_name="Falhou em")
    retry_count = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name="Tentativas"
    )
    provider_response = models.JSONField(
        default=dict, blank=True, verbose_name="Resposta do provedor"
    )
    error_message = models.TextField(blank=True, verbose_name="Erro")
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Tipo relacionado",
    )
    related_object_id = models.PositiveBigIntegerField(
        blank=True, null=True, verbose_name="ID relacionado"
    )
    related_object = GenericForeignKey("related_content_type", "related_object_id")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_message_queue",
        blank=True,
        null=True,
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Mensagem na fila"
        verbose_name_plural = "Fila de mensagens"
        ordering = ["scheduled_at", "id"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["customer", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_channel_display()} para {self.recipient} - {self.get_status_display()}"


class MessageLog(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="message_logs",
        blank=True,
        null=True,
        verbose_name="Cliente",
    )
    queue_message = models.ForeignKey(
        MessageQueue,
        on_delete=models.SET_NULL,
        related_name="logs",
        blank=True,
        null=True,
        verbose_name="Mensagem da fila",
    )
    channel = models.CharField(
        max_length=20, choices=MessageChannel.choices, verbose_name="Canal"
    )
    message_type = models.CharField(
        max_length=30, choices=MessageType.choices, verbose_name="Tipo"
    )
    recipient = models.CharField(max_length=180, verbose_name="Destinatário")
    subject = models.CharField(max_length=180, blank=True, verbose_name="Assunto")
    body_snapshot = models.TextField(verbose_name="Snapshot do corpo")
    status = models.CharField(
        max_length=20, choices=MessageStatus.choices, verbose_name="Status"
    )
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Enviada em")
    provider = models.CharField(max_length=120, blank=True, verbose_name="Provedor")
    provider_message_id = models.CharField(
        max_length=180, blank=True, verbose_name="ID no provedor"
    )
    error_message = models.TextField(blank=True, verbose_name="Erro")
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Tipo relacionado",
    )
    related_object_id = models.PositiveBigIntegerField(
        blank=True, null=True, verbose_name="ID relacionado"
    )
    related_object = GenericForeignKey("related_content_type", "related_object_id")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_message_logs",
        blank=True,
        null=True,
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Log de mensagem"
        verbose_name_plural = "Logs de mensagens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_channel_display()} para {self.recipient} - {self.get_status_display()}"


class MessageEvent(models.Model):
    log = models.ForeignKey(
        MessageLog, on_delete=models.CASCADE, related_name="events", verbose_name="Log"
    )
    event_type = models.CharField(max_length=80, verbose_name="Tipo do evento")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Payload")
    occurred_at = models.DateTimeField(default=timezone.now, verbose_name="Ocorreu em")

    class Meta:
        verbose_name = "Evento de mensagem"
        verbose_name_plural = "Eventos de mensagem"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.event_type} - {self.occurred_at:%d/%m/%Y %H:%M}"


class MessageAttachment(models.Model):
    queue_message = models.ForeignKey(
        MessageQueue,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="Mensagem",
    )
    file = models.FileField(upload_to="mensagens/anexos/%Y/%m/", verbose_name="Arquivo")
    original_name = models.CharField(max_length=180, verbose_name="Nome original")
    content_type = models.CharField(
        max_length=120, blank=True, verbose_name="Tipo de conteúdo"
    )
    size_bytes = models.PositiveIntegerField(default=0, verbose_name="Tamanho em bytes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Anexo de mensagem"
        verbose_name_plural = "Anexos de mensagem"

    def __str__(self):
        return self.original_name


class MessageVariable(models.Model):
    code = models.SlugField(max_length=80, unique=True, verbose_name="Código")
    label = models.CharField(max_length=120, verbose_name="Nome exibido")
    description = models.TextField(blank=True, verbose_name="Descrição")
    category = models.CharField(
        max_length=80, default="Geral", verbose_name="Categoria"
    )
    example_value = models.CharField(max_length=180, blank=True, verbose_name="Exemplo")
    source_path = models.CharField(
        max_length=180,
        blank=True,
        verbose_name="Origem técnica",
        help_text="Ex.: customer.name, service_order.number ou invoice.total_amount.",
    )
    is_sensitive = models.BooleanField(default=False, verbose_name="Dado sensível")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Variável de mensagem"
        verbose_name_plural = "Variáveis de mensagem"
        ordering = ["category", "code"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    @property
    def placeholder(self):
        return "{{ " + self.code + " }}"

    def __str__(self):
        return f"{self.placeholder} - {self.label}"
