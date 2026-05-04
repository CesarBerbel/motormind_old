from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Registro central de auditoria do MotorMind.

    Este model guarda eventos relevantes do sistema sem assumir propriedade
    dos dados dos módulos de negócio. Outros apps chamam auditoria.services
    para registrar ações críticas.
    """

    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login realizado"
        LOGIN_FAILED = "login_failed", "Falha de login"
        LOGOUT = "logout", "Logout"
        CREATE = "create", "Criação"
        UPDATE = "update", "Alteração"
        DELETE = "delete", "Exclusão"
        STATUS_CHANGE = "status_change", "Mudança de status"
        SERVICE_ORDER_OPENED = "service_order_opened", "Abertura de OS"
        SERVICE_ORDER_CANCELED = "service_order_canceled", "Cancelamento de OS"
        STOCK_MOVEMENT = "stock_movement", "Movimentação de estoque"
        PAYMENT_REGISTERED = "payment_registered", "Pagamento registrado"
        EXPENSE_REGISTERED = "expense_registered", "Despesa registrada"
        AI_USED = "ai_used", "Uso de IA"
        MESSAGE_SENT = "message_sent", "Mensagem enviada"
        PERMISSION_DENIED = "permission_denied", "Acesso negado"
        OTHER = "other", "Outro"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        blank=True,
        null=True,
        verbose_name="Usuário",
    )
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        db_index=True,
        verbose_name="Ação",
    )
    app_label = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="App",
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Modelo",
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="ID do objeto",
    )
    object_repr = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Representação do objeto",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Tipo de conteúdo",
    )
    old_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Dados antigos",
    )
    new_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Dados novos",
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Metadados",
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Endereço IP",
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User agent",
    )
    path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Caminho",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Criado em",
    )

    class Meta:
        verbose_name = "Registro de auditoria"
        verbose_name_plural = "Registros de auditoria"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["app_label", "model_name", "object_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        target = self.object_repr or self.object_id or "sem objeto"
        return f"{self.get_action_display()} - {target}"
