from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_service_order_numbers(apps, schema_editor):
    ServiceOrder = apps.get_model("service_orders", "ServiceOrder")

    for service_order in ServiceOrder.objects.order_by("pk"):
        if service_order.number:
            continue

        created_at = service_order.created_at
        year = created_at.year if created_at else 2026
        service_order.number = f"OS-{year}-{service_order.pk:06d}"
        service_order.save(update_fields=["number"])


def clear_service_order_numbers(apps, schema_editor):
    ServiceOrder = apps.get_model("service_orders", "ServiceOrder")
    ServiceOrder.objects.update(number=None)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("service_orders", "0006_serviceordertimeentry"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorder",
            name="number",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=20,
                null=True,
                unique=True,
                verbose_name="Número da OS",
            ),
        ),
        migrations.AlterField(
            model_name="serviceorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Aberta"),
                    ("in_progress", "Em execução"),
                    ("waiting_parts", "Aguardando peças"),
                    ("waiting_approval", "Aguardando aprovação"),
                    ("approved", "Aprovada"),
                    ("finished", "Finalizada"),
                    ("canceled", "Cancelada"),
                ],
                default="open",
                max_length=30,
                verbose_name="Status",
            ),
        ),
        migrations.CreateModel(
            name="ServiceOrderApproval",
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
                        choices=[
                            ("in_person", "Presencial"),
                            ("phone", "Telefone"),
                            ("whatsapp", "WhatsApp"),
                            ("email", "E-mail"),
                            ("portal", "Portal do cliente"),
                            ("other", "Outro"),
                        ],
                        max_length=20,
                        verbose_name="Canal de aprovação",
                    ),
                ),
                (
                    "customer_name_snapshot",
                    models.CharField(
                        max_length=255,
                        verbose_name="Nome do cliente no momento da aprovação",
                    ),
                ),
                (
                    "vehicle_snapshot",
                    models.CharField(
                        max_length=255,
                        verbose_name="Veículo no momento da aprovação",
                    ),
                ),
                (
                    "gross_total",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Total bruto aprovado",
                    ),
                ),
                (
                    "discount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=10,
                        verbose_name="Desconto aprovado",
                    ),
                ),
                (
                    "net_total",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Total líquido aprovado",
                    ),
                ),
                (
                    "financial_summary_snapshot",
                    models.JSONField(
                        default=dict,
                        verbose_name="Snapshot financeiro aprovado",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        verbose_name="Observações da aprovação",
                    ),
                ),
                (
                    "approved_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Aprovado em",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Criado em",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Atualizado em",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approved_service_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Aprovado por",
                    ),
                ),
                (
                    "service_order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approval",
                        to="service_orders.serviceorder",
                        verbose_name="Ordem de serviço",
                    ),
                ),
            ],
            options={
                "verbose_name": "Aprovação de orçamento da OS",
                "verbose_name_plural": "Aprovações de orçamento das OS",
                "ordering": ["-approved_at"],
            },
        ),
        migrations.RunPython(
            populate_service_order_numbers,
            reverse_code=clear_service_order_numbers,
        ),
    ]
