from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from core.models import SoftDeleteModel


class AIUseCase(models.TextChoices):
    SERVICE_ORDER_DESCRIPTION = "service_order_description", "Descrição de OS"
    TECHNICAL_DIAGNOSIS = "technical_diagnosis", "Diagnóstico técnico"
    TECHNICAL_REPORT = "technical_report", "Relatório técnico"
    CUSTOMER_MESSAGE = "customer_message", "Mensagem para cliente"
    CRM_ANALYSIS = "crm_analysis", "Análise de CRM"
    CAMPAIGN_SUGGESTION = "campaign_suggestion", "Sugestão de campanha"
    CUSTOMER_HISTORY_SUMMARY = "customer_history_summary", "Resumo do histórico"
    FREE_ASSISTANT = "free_assistant", "Assistente livre"


class AIRequestStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PROCESSING = "processing", "Processando"
    COMPLETED = "completed", "Concluída"
    FAILED = "failed", "Falhou"


class AIReviewStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Rejeitada"
    EDITED = "edited", "Editada"


class AIPromptTemplate(SoftDeleteModel):
    name = models.CharField("nome", max_length=120)
    code = models.SlugField("código", max_length=120)
    use_case = models.CharField("caso de uso", max_length=60, choices=AIUseCase.choices)
    version = models.PositiveIntegerField("versão", default=1)
    system_prompt = models.TextField("prompt do sistema")
    user_prompt_template = models.TextField("template do prompt do usuário")
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "template de prompt de IA"
        verbose_name_plural = "templates de prompt de IA"
        ordering = ["use_case", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["code", "version"],
                name="ai_unique_prompt_code_version",
            )
        ]
        indexes = [
            models.Index(fields=["use_case", "is_active"]),
            models.Index(fields=["code", "version"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class AIRequest(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuário",
        on_delete=models.PROTECT,
        related_name="ai_requests",
    )
    prompt_template = models.ForeignKey(
        AIPromptTemplate,
        verbose_name="template de prompt",
        on_delete=models.PROTECT,
        related_name="requests",
        null=True,
        blank=True,
    )
    use_case = models.CharField("caso de uso", max_length=60, choices=AIUseCase.choices)
    input_data = models.JSONField("dados de entrada", default=dict)
    rendered_prompt = models.TextField("prompt renderizado", blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=AIRequestStatus.choices,
        default=AIRequestStatus.PENDING,
    )
    error_message = models.TextField("mensagem de erro", blank=True)
    related_content_type = models.ForeignKey(
        ContentType,
        verbose_name="tipo do objeto relacionado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_object_id = models.PositiveBigIntegerField(
        "id do objeto relacionado", null=True, blank=True
    )
    related_object = GenericForeignKey("related_content_type", "related_object_id")
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "requisição de IA"
        verbose_name_plural = "requisições de IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["use_case", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"IA #{self.pk} - {self.get_use_case_display()}"


class AIResponse(SoftDeleteModel):
    request = models.OneToOneField(
        AIRequest,
        verbose_name="requisição",
        on_delete=models.CASCADE,
        related_name="response",
    )
    output_text = models.TextField("resposta gerada")
    model_name = models.CharField("modelo", max_length=120, blank=True)
    tokens_input = models.PositiveIntegerField("tokens de entrada", default=0)
    tokens_output = models.PositiveIntegerField("tokens de saída", default=0)
    latency_ms = models.PositiveIntegerField("latência em ms", default=0)
    raw_response = models.JSONField("resposta bruta", default=dict, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "resposta de IA"
        verbose_name_plural = "respostas de IA"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Resposta da {self.request}"


class AIUsageLog(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuário",
        on_delete=models.PROTECT,
        related_name="ai_usage_logs",
    )
    feature = models.CharField("funcionalidade", max_length=120)
    use_case = models.CharField("caso de uso", max_length=60, choices=AIUseCase.choices)
    status = models.CharField("status", max_length=20, choices=AIRequestStatus.choices)
    related_content_type = models.ForeignKey(
        ContentType,
        verbose_name="tipo do objeto relacionado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_object_id = models.PositiveBigIntegerField(
        "id do objeto relacionado", null=True, blank=True
    )
    related_object = GenericForeignKey("related_content_type", "related_object_id")
    metadata = models.JSONField("metadados", default=dict, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "log de uso de IA"
        verbose_name_plural = "logs de uso de IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["feature", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.feature} - {self.get_status_display()}"


class AIReview(SoftDeleteModel):
    response = models.OneToOneField(
        AIResponse,
        verbose_name="resposta",
        on_delete=models.CASCADE,
        related_name="review",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="revisado por",
        on_delete=models.PROTECT,
        related_name="ai_reviews",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=AIReviewStatus.choices,
        default=AIReviewStatus.PENDING,
    )
    edited_output_text = models.TextField("texto editado", blank=True)
    notes = models.TextField("observações", blank=True)
    reviewed_at = models.DateTimeField("revisado em", default=timezone.now)

    class Meta:
        verbose_name = "revisão de IA"
        verbose_name_plural = "revisões de IA"
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"Revisão {self.get_status_display()} da resposta #{self.response_id}"
