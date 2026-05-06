# Generated for MotorMind catalog intelligence package.
# Safe migration: avoids duplicate column errors when service_order_item_id
# already exists because an earlier patch/migration created it.

from django.db import migrations, models, connection
import django.db.models.deletion


def add_service_order_item_column_if_missing(apps, schema_editor):
    table_name = "inventory_serviceorderpart"
    column_name = "service_order_item_id"

    existing_columns = {
        column.name
        for column in connection.introspection.get_table_description(
            schema_editor.connection.cursor(), table_name
        )
    }

    if column_name in existing_columns:
        return

    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" bigint NULL'
        )
        schema_editor.execute(
            f'CREATE INDEX IF NOT EXISTS "{table_name}_{column_name}_idx" '
            f'ON "{table_name}" ("{column_name}")'
        )
        return

    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" bigint NULL'
        )
        schema_editor.execute(
            f'CREATE INDEX IF NOT EXISTS "{table_name}_{column_name}_idx" '
            f'ON "{table_name}" ("{column_name}")'
        )
        return

    schema_editor.execute(
        f'ALTER TABLE {table_name} ADD COLUMN {column_name} bigint NULL'
    )


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0009_serviceorder_deleted_at_and_more"),
        ("inventory", "0004_partbrand_partcategory_refactor"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_service_order_item_column_if_missing,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="serviceorderpart",
                    name="service_order_item",
                    field=models.ForeignKey(
                        blank=True,
                        help_text="Serviço específico da OS que originou esta peça.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_parts",
                        to="service_orders.serviceorderitem",
                        verbose_name="Serviço da OS",
                    ),
                ),
            ],
        ),
    ]
