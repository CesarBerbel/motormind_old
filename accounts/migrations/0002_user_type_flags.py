from django.db import migrations, models


def classify_existing_users(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")

    for user in CustomUser.objects.all():
        if user.is_superuser:
            user.is_customer = False
            user.is_employee = False
        else:
            user.is_customer = False
            user.is_employee = True
        user.save(update_fields=["is_customer", "is_employee"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_customer",
            field=models.BooleanField(
                default=False,
                help_text="Marque quando este usuário representa um cliente no portal.",
                verbose_name="Cliente",
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="is_employee",
            field=models.BooleanField(
                default=True,
                help_text="Marque quando este usuário representa um funcionário da oficina.",
                verbose_name="Funcionário",
            ),
        ),
        migrations.RunPython(classify_existing_users, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("is_superuser", False))
                    | (models.Q(("is_customer", False)) & models.Q(("is_employee", False)))
                ),
                name="accounts_superuser_not_customer_or_employee",
            ),
        ),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.CheckConstraint(
                condition=models.Q(("is_customer", False)) | models.Q(("is_employee", False)),
                name="accounts_user_not_customer_and_employee",
            ),
        ),
    ]
