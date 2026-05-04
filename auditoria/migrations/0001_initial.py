# Generated manually for MotorMind audit module.

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
            name="AuditLog",
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
                    "action",
                    models.CharField(
                        choices=[
                            ("login_success", "Login realizado"),
                            ("login_failed", "Falha de login"),
                            ("logout", "Logout"),
                            ("create", "Criação"),
                            ("update", "Alteração"),
                            ("delete", "Exclusão"),
                            ("status_change", "Mudança de status"),
                            ("service_order_opened", "Abertura de OS"),
                            ("service_order_canceled", "Cancelamento de OS"),
                            ("stock_movement", "Movimentação de estoque"),
                            ("payment_registered", "Pagamento registrado"),
                            ("expense_registered", "Despesa registrada"),
                            ("ai_used", "Uso de IA"),
                            ("message_sent", "Mensagem enviada"),
                            ("permission_denied", "Acesso negado"),
                            ("other", "Outro"),
                        ],
                        db_index=True,
                        max_length=50,
                        verbose_name="Ação",
                    ),
                ),
                (
                    "app_label",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=100,
                        verbose_name="App",
                    ),
                ),
                (
                    "model_name",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=100,
                        verbose_name="Modelo",
                    ),
                ),
                (
                    "object_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=100,
                        verbose_name="ID do objeto",
                    ),
                ),
                (
                    "object_repr",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Representação do objeto",
                    ),
                ),
                (
                    "old_data",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Dados antigos",
                    ),
                ),
                (
                    "new_data",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Dados novos",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Metadados",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        verbose_name="Endereço IP",
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        verbose_name="User agent",
                    ),
                ),
                (
                    "path",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Caminho",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        verbose_name="Criado em",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="Tipo de conteúdo",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de auditoria",
                "verbose_name_plural": "Registros de auditoria",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["action", "created_at"], name="auditoria_a_action_844d0a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["app_label", "model_name", "object_id"],
                name="auditoria_a_app_lab_441fdb_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["user", "created_at"], name="auditoria_a_user_id_e60460_idx"
            ),
        ),
    ]
