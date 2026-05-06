# Generated manually for MotorMind.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0003_serviceorderitem"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorderpart",
            name="service_order_item",
            field=models.ForeignKey(
                blank=True,
                help_text="Serviço da OS que originou esta peça.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="linked_parts",
                to="service_orders.serviceorderitem",
                verbose_name="Serviço da OS",
            ),
        ),
    ]
