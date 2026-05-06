# Generated manually for MotorMind.

from decimal import Decimal

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
        ("workshop_services", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkshopServicePart",
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
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Excluído em"
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("1.00"),
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Quantidade padrão",
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Deixe vazio para usar o preço de venda atual da peça.",
                        max_digits=10,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                        verbose_name="Preço unitário",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativa")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criada em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizada em"),
                ),
                (
                    "part",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workshop_service_templates",
                        to="inventory.part",
                        verbose_name="Peça",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="default_parts",
                        to="workshop_services.workshopservice",
                        verbose_name="Serviço",
                    ),
                ),
            ],
            options={
                "verbose_name": "Peça padrão do serviço",
                "verbose_name_plural": "Peças padrão dos serviços",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="workshopservicepart",
            constraint=models.UniqueConstraint(
                fields=("service", "part"),
                name="unique_default_part_per_workshop_service",
            ),
        ),
    ]
