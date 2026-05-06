# Generated for MotorMind catalog intelligence package.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("workshop_services", "0003_service_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="workshopservicecategory",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="children",
                to="workshop_services.workshopservicecategory",
                verbose_name="Categoria pai",
            ),
        ),
        migrations.AddField(
            model_name="workshopservice",
            name="current_version",
            field=models.PositiveIntegerField(default=1, verbose_name="Versão atual"),
        ),
        migrations.CreateModel(
            name="WorkshopServiceVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version_number", models.PositiveIntegerField(verbose_name="Número da versão")),
                ("code_snapshot", models.CharField(max_length=50, verbose_name="Código")),
                ("name_snapshot", models.CharField(max_length=150, verbose_name="Nome")),
                ("category_snapshot", models.CharField(blank=True, max_length=160, verbose_name="Categoria")),
                ("description_snapshot", models.TextField(blank=True, verbose_name="Descrição")),
                ("default_price_snapshot", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Preço padrão")),
                ("estimated_minutes_snapshot", models.PositiveIntegerField(default=0, verbose_name="Tempo estimado")),
                ("parts_snapshot", models.JSONField(blank=True, default=list, verbose_name="Peças da versão")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_workshop_service_versions", to=settings.AUTH_USER_MODEL, verbose_name="Criado por")),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="workshop_services.workshopservice", verbose_name="Serviço")),
            ],
            options={
                "verbose_name": "Versão de serviço",
                "verbose_name_plural": "Versões de serviços",
                "ordering": ["service", "-version_number"],
            },
        ),
        migrations.CreateModel(
            name="WorkshopCatalogAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("service_created", "Serviço criado"), ("service_updated", "Serviço atualizado"), ("service_parts_updated", "Peças do serviço atualizadas"), ("combo_created", "Combo criado"), ("combo_updated", "Combo atualizado"), ("combo_items_updated", "Serviços do combo atualizados"), ("category_created", "Categoria criada"), ("category_updated", "Categoria atualizada")], max_length=40, verbose_name="Ação")),
                ("old_data", models.JSONField(blank=True, default=dict, verbose_name="Dados anteriores")),
                ("new_data", models.JSONField(blank=True, default=dict, verbose_name="Dados novos")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="catalog_audit_logs", to="workshop_services.workshopservicecategory", verbose_name="Categoria")),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workshop_catalog_audit_logs", to=settings.AUTH_USER_MODEL, verbose_name="Alterado por")),
                ("combo", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="catalog_audit_logs", to="workshop_services.servicecombo", verbose_name="Combo")),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="catalog_audit_logs", to="workshop_services.workshopservice", verbose_name="Serviço")),
            ],
            options={
                "verbose_name": "Auditoria do catálogo",
                "verbose_name_plural": "Auditorias do catálogo",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="workshopserviceversion",
            constraint=models.UniqueConstraint(fields=("service", "version_number"), name="unique_version_per_workshop_service"),
        ),
    ]
