# Generated manually for MotorMind service order warranty and opening flow.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0009_serviceorder_deleted_at_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorder",
            name="order_type",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("warranty", "Garantia"),
                    ("return", "Retorno"),
                ],
                default="normal",
                max_length=20,
                verbose_name="Tipo da OS",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="warranty_origin_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="warranty_orders",
                to="service_orders.serviceorder",
                verbose_name="OS original da garantia/retorno",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="warranty_reason",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Motivo da garantia/retorno",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="warranty_approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="approved_warranty_service_orders",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Garantia aprovada por",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="warranty_approved_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Garantia aprovada em",
            ),
        ),
    ]
