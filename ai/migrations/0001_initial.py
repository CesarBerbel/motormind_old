# Generated manually for MotorMind AI module.

import django.contrib.contenttypes.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIPromptTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="nome")),
                ("code", models.SlugField(max_length=120, verbose_name="código")),
                (
                    "use_case",
                    models.CharField(
                        choices=[
                            ("service_order_description", "Descrição de OS"),
                            ("technical_diagnosis", "Diagnóstico técnico"),
                            ("technical_report", "Relatório técnico"),
                            ("customer_message", "Mensagem para cliente"),
                            ("crm_analysis", "Análise de CRM"),
                            ("campaign_suggestion", "Sugestão de campanha"),
                            ("customer_history_summary", "Resumo do histórico"),
                            ("free_assistant", "Assistente livre"),
                        ],
                        max_length=60,
                        verbose_name="caso de uso",
                    ),
                ),
                (
                    "version",
                    models.PositiveIntegerField(default=1, verbose_name="versão"),
                ),
                ("system_prompt", models.TextField(verbose_name="prompt do sistema")),
                (
                    "user_prompt_template",
                    models.TextField(verbose_name="template do prompt do usuário"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="ativo")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="atualizado em"),
                ),
            ],
            options={
                "verbose_name": "template de prompt de IA",
                "verbose_name_plural": "templates de prompt de IA",
                "ordering": ["use_case", "code", "-version"],
            },
        ),
        migrations.CreateModel(
            name="AIRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "use_case",
                    models.CharField(
                        choices=[
                            ("service_order_description", "Descrição de OS"),
                            ("technical_diagnosis", "Diagnóstico técnico"),
                            ("technical_report", "Relatório técnico"),
                            ("customer_message", "Mensagem para cliente"),
                            ("crm_analysis", "Análise de CRM"),
                            ("campaign_suggestion", "Sugestão de campanha"),
                            ("customer_history_summary", "Resumo do histórico"),
                            ("free_assistant", "Assistente livre"),
                        ],
                        max_length=60,
                        verbose_name="caso de uso",
                    ),
                ),
                (
                    "input_data",
                    models.JSONField(default=dict, verbose_name="dados de entrada"),
                ),
                (
                    "rendered_prompt",
                    models.TextField(blank=True, verbose_name="prompt renderizado"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("processing", "Processando"),
                            ("completed", "Concluída"),
                            ("failed", "Falhou"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="mensagem de erro"),
                ),
                (
                    "related_object_id",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="id do objeto relacionado"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="atualizado em"),
                ),
                (
                    "prompt_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requests",
                        to="ai.aiprompttemplate",
                        verbose_name="template de prompt",
                    ),
                ),
                (
                    "related_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="tipo do objeto relacionado",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ai_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "requisição de IA",
                "verbose_name_plural": "requisições de IA",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIResponse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("output_text", models.TextField(verbose_name="resposta gerada")),
                (
                    "model_name",
                    models.CharField(blank=True, max_length=120, verbose_name="modelo"),
                ),
                (
                    "tokens_input",
                    models.PositiveIntegerField(
                        default=0, verbose_name="tokens de entrada"
                    ),
                ),
                (
                    "tokens_output",
                    models.PositiveIntegerField(
                        default=0, verbose_name="tokens de saída"
                    ),
                ),
                (
                    "latency_ms",
                    models.PositiveIntegerField(
                        default=0, verbose_name="latência em ms"
                    ),
                ),
                (
                    "raw_response",
                    models.JSONField(
                        blank=True, default=dict, verbose_name="resposta bruta"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response",
                        to="ai.airequest",
                        verbose_name="requisição",
                    ),
                ),
            ],
            options={
                "verbose_name": "resposta de IA",
                "verbose_name_plural": "respostas de IA",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIUsageLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "feature",
                    models.CharField(max_length=120, verbose_name="funcionalidade"),
                ),
                (
                    "use_case",
                    models.CharField(
                        choices=[
                            ("service_order_description", "Descrição de OS"),
                            ("technical_diagnosis", "Diagnóstico técnico"),
                            ("technical_report", "Relatório técnico"),
                            ("customer_message", "Mensagem para cliente"),
                            ("crm_analysis", "Análise de CRM"),
                            ("campaign_suggestion", "Sugestão de campanha"),
                            ("customer_history_summary", "Resumo do histórico"),
                            ("free_assistant", "Assistente livre"),
                        ],
                        max_length=60,
                        verbose_name="caso de uso",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("processing", "Processando"),
                            ("completed", "Concluída"),
                            ("failed", "Falhou"),
                        ],
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "related_object_id",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="id do objeto relacionado"
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True, default=dict, verbose_name="metadados"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "related_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="tipo do objeto relacionado",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ai_usage_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "log de uso de IA",
                "verbose_name_plural": "logs de uso de IA",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIReview",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("approved", "Aprovada"),
                            ("rejected", "Rejeitada"),
                            ("edited", "Editada"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "edited_output_text",
                    models.TextField(blank=True, verbose_name="texto editado"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="observações")),
                (
                    "reviewed_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="revisado em"
                    ),
                ),
                (
                    "response",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review",
                        to="ai.airesponse",
                        verbose_name="resposta",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ai_reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="revisado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "revisão de IA",
                "verbose_name_plural": "revisões de IA",
                "ordering": ["-reviewed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="aiprompttemplate",
            index=models.Index(
                fields=["use_case", "is_active"], name="ai_aiprompt_use_ca_0d8f1a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aiprompttemplate",
            index=models.Index(
                fields=["code", "version"], name="ai_aiprompt_code_3f9a62_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="aiprompttemplate",
            constraint=models.UniqueConstraint(
                fields=("code", "version"), name="ai_unique_prompt_code_version"
            ),
        ),
        migrations.AddIndex(
            model_name="airequest",
            index=models.Index(
                fields=["use_case", "status"], name="ai_aireques_use_ca_59c0bb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="airequest",
            index=models.Index(
                fields=["created_at"], name="ai_aireques_created_54fca5_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aiusagelog",
            index=models.Index(
                fields=["feature", "status"], name="ai_aiusage_feature_41ab75_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aiusagelog",
            index=models.Index(
                fields=["created_at"], name="ai_aiusage_created_7bc31e_idx"
            ),
        ),
    ]
