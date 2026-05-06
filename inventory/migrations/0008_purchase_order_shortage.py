# Generated for automatic purchase orders when OS part demand exceeds stock.

import decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0007_alter_serviceorderpart_service_order_item"),
        ("service_orders", "0009_serviceorder_deleted_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorderpart",
            name="reserved_quantity",
            field=models.DecimalField(
                decimal_places=2,
                default=decimal.Decimal("0.00"),
                help_text=(
                    "Quantidade efetivamente baixada/reservada do estoque. "
                    "A diferença abre pedido de compra."
                ),
                max_digits=10,
                validators=[
                    django.core.validators.MinValueValidator(decimal.Decimal("0.00"))
                ],
                verbose_name="Quantidade reservada em estoque",
            ),
        ),
        migrations.AlterField(
            model_name="serviceorderpart",
            name="quantity",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[
                    django.core.validators.MinValueValidator(decimal.Decimal("0.01"))
                ],
                verbose_name="Quantidade solicitada",
            ),
        ),
        migrations.AlterField(
            model_name="serviceorderpart",
            name="status",
            field=models.CharField(
                choices=[
                    ("reserved", "Reservada"),
                    ("waiting_purchase", "Aguardando compra"),
                    ("used", "Usada"),
                    ("returned", "Devolvida"),
                    ("canceled", "Cancelada"),
                ],
                default="reserved",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
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
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "requested_quantity",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(
                                decimal.Decimal("0.01")
                            )
                        ],
                        verbose_name="Quantidade a comprar",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Aberto"),
                            ("ordered", "Compra solicitada"),
                            ("received", "Recebido"),
                            ("canceled", "Cancelado"),
                        ],
                        default="open",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("reason", models.TextField(verbose_name="Motivo")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_purchase_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "part",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="inventory.part",
                        verbose_name="Peça",
                    ),
                ),
                (
                    "service_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="service_orders.serviceorder",
                        verbose_name="Ordem de serviço",
                    ),
                ),
                (
                    "service_order_part",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="inventory.serviceorderpart",
                        verbose_name="Peça da OS",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pedido de compra",
                "verbose_name_plural": "Pedidos de compra",
                "ordering": ["-created_at"],
            },
        ),
    ]
