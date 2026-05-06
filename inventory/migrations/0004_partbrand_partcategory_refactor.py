from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_brand_category(apps, schema_editor):
    Part = apps.get_model("inventory", "Part")
    PartBrand = apps.get_model("inventory", "PartBrand")
    PartCategory = apps.get_model("inventory", "PartCategory")

    for part in Part.objects.all():
        if getattr(part, "brand", None):
            brand, _ = PartBrand.objects.get_or_create(
                name=part.brand,
                defaults={"is_active": True},
            )
            part.brand_ref = brand

        if getattr(part, "category", None):
            category, _ = PartCategory.objects.get_or_create(
                name=part.category,
                defaults={"description": "", "is_active": True},
            )
            part.category_ref = category

        part.save(update_fields=["brand_ref", "category_ref"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_part_deleted_at_serviceorderpart_deleted_at_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PartBrand",
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
                    models.CharField(
                        max_length=80, unique=True, verbose_name="Nome da marca"
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
            ],
            options={
                "verbose_name": "Marca de peça",
                "verbose_name_plural": "Marcas de peças",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PartCategory",
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
                    models.CharField(
                        max_length=80, unique=True, verbose_name="Nome da categoria"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
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
                "verbose_name": "Categoria de peça",
                "verbose_name_plural": "Categorias de peças",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="part",
            name="brand_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parts_ref",
                to="inventory.partbrand",
                verbose_name="Marca",
            ),
        ),
        migrations.AddField(
            model_name="part",
            name="category_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parts_ref",
                to="inventory.partcategory",
                verbose_name="Categoria",
            ),
        ),
        migrations.RunPython(migrate_existing_brand_category, noop_reverse),
        migrations.RemoveField(model_name="part", name="brand"),
        migrations.RemoveField(model_name="part", name="category"),
        migrations.RenameField(
            model_name="part", old_name="brand_ref", new_name="brand"
        ),
        migrations.RenameField(
            model_name="part", old_name="category_ref", new_name="category"
        ),
        migrations.AlterField(
            model_name="part",
            name="brand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parts",
                to="inventory.partbrand",
                verbose_name="Marca",
            ),
        ),
        migrations.AlterField(
            model_name="part",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parts",
                to="inventory.partcategory",
                verbose_name="Categoria",
            ),
        ),
    ]
