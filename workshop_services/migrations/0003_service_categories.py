# Generated manually for MotorMind.

import django.db.models.deletion
from django.db import migrations, models


def migrate_text_categories_to_catalog(apps, schema_editor):
    WorkshopService = apps.get_model("workshop_services", "WorkshopService")
    WorkshopServiceCategory = apps.get_model(
        "workshop_services", "WorkshopServiceCategory"
    )

    category_cache = {}

    for service in WorkshopService.objects.exclude(category__isnull=True).exclude(
        category=""
    ):
        category_name = service.category.strip()
        if not category_name:
            continue

        category = category_cache.get(category_name)
        if category is None:
            category, _created = WorkshopServiceCategory.objects.get_or_create(
                name=category_name,
                defaults={"is_active": True},
            )
            category_cache[category_name] = category

        service.category_ref = category
        service.save(update_fields=["category_ref"])


class Migration(migrations.Migration):

    dependencies = [
        ("workshop_services", "0002_workshopservicepart"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkshopServiceCategory",
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
                        blank=True, db_index=True, null=True, verbose_name="Excluído em"
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=80, unique=True, verbose_name="Nome"),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Descrição"),
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
            ],
            options={
                "verbose_name": "Categoria de serviço",
                "verbose_name_plural": "Categorias de serviços",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="workshopservice",
            name="category_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="services",
                to="workshop_services.workshopservicecategory",
                verbose_name="Categoria",
            ),
        ),
        migrations.RunPython(
            migrate_text_categories_to_catalog, migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="workshopservice",
            name="category",
        ),
        migrations.RenameField(
            model_name="workshopservice",
            old_name="category_ref",
            new_name="category",
        ),
    ]
