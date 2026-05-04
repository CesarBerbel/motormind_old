import django.contrib.contenttypes.fields
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageProvider",
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
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="Nome"),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "settings",
                    models.JSONField(
                        blank=True, default=dict, verbose_name="Configurações"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
            ],
            options={
                "verbose_name": "Provedor de mensagem",
                "verbose_name_plural": "Provedores de mensagem",
                "ordering": ["channel", "name"],
            },
        ),
        migrations.CreateModel(
            name="MessageTemplate",
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
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                (
                    "code",
                    models.SlugField(max_length=80, unique=True, verbose_name="Código"),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("transactional", "Transacional"),
                            ("marketing", "Comercial"),
                            ("relationship", "Relacionamento"),
                            ("system", "Sistema"),
                            ("manual", "Manual"),
                            ("automatic", "Automática"),
                        ],
                        max_length=30,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, max_length=180, verbose_name="Assunto"
                    ),
                ),
                ("body", models.TextField(verbose_name="Corpo")),
                (
                    "available_variables",
                    models.JSONField(
                        blank=True, default=list, verbose_name="Variáveis disponíveis"
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
            ],
            options={
                "verbose_name": "Template de mensagem",
                "verbose_name_plural": "Templates de mensagem",
                "ordering": ["channel", "name"],
            },
        ),
        migrations.CreateModel(
            name="MessagePreference",
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
                    "accepts_email_transactional",
                    models.BooleanField(
                        default=True, verbose_name="Aceita e-mail transacional"
                    ),
                ),
                (
                    "accepts_whatsapp_transactional",
                    models.BooleanField(
                        default=True, verbose_name="Aceita WhatsApp transacional"
                    ),
                ),
                (
                    "accepts_email_marketing",
                    models.BooleanField(
                        default=False, verbose_name="Aceita e-mail comercial"
                    ),
                ),
                (
                    "accepts_whatsapp_marketing",
                    models.BooleanField(
                        default=False, verbose_name="Aceita WhatsApp comercial"
                    ),
                ),
                (
                    "preferred_channel",
                    models.CharField(
                        choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                        default="whatsapp",
                        max_length=20,
                        verbose_name="Canal preferido",
                    ),
                ),
                (
                    "consent_source",
                    models.CharField(
                        blank=True,
                        max_length=120,
                        verbose_name="Origem do consentimento",
                    ),
                ),
                (
                    "consent_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data do consentimento"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_preference",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Preferência de mensagem",
                "verbose_name_plural": "Preferências de mensagem",
            },
        ),
        migrations.CreateModel(
            name="MessageQueue",
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
                    "channel",
                    models.CharField(
                        choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("transactional", "Transacional"),
                            ("marketing", "Comercial"),
                            ("relationship", "Relacionamento"),
                            ("system", "Sistema"),
                            ("manual", "Manual"),
                            ("automatic", "Automática"),
                        ],
                        max_length=30,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "recipient",
                    models.CharField(max_length=180, verbose_name="Destinatário"),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, max_length=180, verbose_name="Assunto"
                    ),
                ),
                ("body", models.TextField(verbose_name="Corpo")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("pending", "Pendente"),
                            ("processing", "Processando"),
                            ("sent", "Enviada"),
                            ("failed", "Falhou"),
                            ("canceled", "Cancelada"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "scheduled_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Agendada para"
                    ),
                ),
                (
                    "sent_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Enviada em"
                    ),
                ),
                (
                    "failed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Falhou em"
                    ),
                ),
                (
                    "retry_count",
                    models.PositiveSmallIntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Tentativas",
                    ),
                ),
                (
                    "provider_response",
                    models.JSONField(
                        blank=True, default=dict, verbose_name="Resposta do provedor"
                    ),
                ),
                ("error_message", models.TextField(blank=True, verbose_name="Erro")),
                (
                    "related_object_id",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="ID relacionado"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criada em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizada em"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_message_queue",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="message_queue",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "related_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="Tipo relacionado",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="queued_messages",
                        to="mensagens.messagetemplate",
                        verbose_name="Template",
                    ),
                ),
            ],
            options={
                "verbose_name": "Mensagem na fila",
                "verbose_name_plural": "Fila de mensagens",
                "ordering": ["scheduled_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="MessageLog",
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
                    "channel",
                    models.CharField(
                        choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("transactional", "Transacional"),
                            ("marketing", "Comercial"),
                            ("relationship", "Relacionamento"),
                            ("system", "Sistema"),
                            ("manual", "Manual"),
                            ("automatic", "Automática"),
                        ],
                        max_length=30,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "recipient",
                    models.CharField(max_length=180, verbose_name="Destinatário"),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, max_length=180, verbose_name="Assunto"
                    ),
                ),
                ("body_snapshot", models.TextField(verbose_name="Snapshot do corpo")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("pending", "Pendente"),
                            ("processing", "Processando"),
                            ("sent", "Enviada"),
                            ("failed", "Falhou"),
                            ("canceled", "Cancelada"),
                        ],
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "sent_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Enviada em"
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        blank=True, max_length=120, verbose_name="Provedor"
                    ),
                ),
                (
                    "provider_message_id",
                    models.CharField(
                        blank=True, max_length=180, verbose_name="ID no provedor"
                    ),
                ),
                ("error_message", models.TextField(blank=True, verbose_name="Erro")),
                (
                    "related_object_id",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="ID relacionado"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_message_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="message_logs",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "queue_message",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="logs",
                        to="mensagens.messagequeue",
                        verbose_name="Mensagem da fila",
                    ),
                ),
                (
                    "related_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="Tipo relacionado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Log de mensagem",
                "verbose_name_plural": "Logs de mensagens",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MessageEvent",
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
                    "event_type",
                    models.CharField(max_length=80, verbose_name="Tipo do evento"),
                ),
                (
                    "payload",
                    models.JSONField(blank=True, default=dict, verbose_name="Payload"),
                ),
                (
                    "occurred_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Ocorreu em"
                    ),
                ),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="mensagens.messagelog",
                        verbose_name="Log",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento de mensagem",
                "verbose_name_plural": "Eventos de mensagem",
                "ordering": ["-occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="MessageAttachment",
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
                    "file",
                    models.FileField(
                        upload_to="mensagens/anexos/%Y/%m/", verbose_name="Arquivo"
                    ),
                ),
                (
                    "original_name",
                    models.CharField(max_length=180, verbose_name="Nome original"),
                ),
                (
                    "content_type",
                    models.CharField(
                        blank=True, max_length=120, verbose_name="Tipo de conteúdo"
                    ),
                ),
                (
                    "size_bytes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Tamanho em bytes"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "queue_message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="mensagens.messagequeue",
                        verbose_name="Mensagem",
                    ),
                ),
            ],
            options={
                "verbose_name": "Anexo de mensagem",
                "verbose_name_plural": "Anexos de mensagem",
            },
        ),
        migrations.AddIndex(
            model_name="messagetemplate",
            index=models.Index(
                fields=["code", "is_active"], name="mensagens_m_code_3651d8_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="messagequeue",
            index=models.Index(
                fields=["status", "scheduled_at"], name="mensagens_m_status_3dce64_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="messagequeue",
            index=models.Index(
                fields=["customer", "-created_at"],
                name="mensagens_m_custome_31df55_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="messagelog",
            index=models.Index(
                fields=["customer", "-created_at"],
                name="mensagens_m_custome_642622_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="messagelog",
            index=models.Index(
                fields=["status", "-created_at"], name="mensagens_m_status_546a15_idx"
            ),
        ),
    ]
