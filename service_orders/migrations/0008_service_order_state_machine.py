# Generated manually for MotorMind service order state machine.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0007_serviceorder_number_approval"),
    ]

    operations = [
        migrations.AlterField(
            model_name="serviceorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Aberta"),
                    ("in_diagnosis", "Em diagnóstico"),
                    ("waiting_approval", "Aguardando aprovação"),
                    ("approved", "Aprovada"),
                    ("in_progress", "Em execução"),
                    ("waiting_parts", "Aguardando peças"),
                    ("finished", "Finalizada"),
                    ("billed", "Faturada"),
                    ("paid", "Paga"),
                    ("canceled", "Cancelada"),
                ],
                default="open",
                max_length=30,
                verbose_name="Status",
            ),
        ),
    ]
