# Generated manually for MotorMind CRM on 2026-05-04

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("service_orders", "0006_serviceordertimeentry"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Campaign",
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
                ("name", models.CharField(max_length=150, verbose_name="Nome")),
                (
                    "campaign_type",
                    models.CharField(
                        choices=[
                            ("post_sale", "Pós-venda"),
                            ("preventive_maintenance", "Revisão preventiva"),
                            ("inactive_customers", "Clientes inativos"),
                            ("promotion", "Promoção"),
                            ("birthday", "Aniversário"),
                        ],
                        max_length=40,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("email", "E-mail"),
                            ("whatsapp", "WhatsApp"),
                            ("phone", "Telefone"),
                        ],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                ("subject", models.CharField(max_length=150, verbose_name="Assunto")),
                ("message", models.TextField(verbose_name="Mensagem")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("scheduled", "Agendada"),
                            ("running", "Em execução"),
                            ("finished", "Finalizada"),
                            ("canceled", "Cancelada"),
                        ],
                        default="draft",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "scheduled_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Agendada para"
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Iniciada em"
                    ),
                ),
                (
                    "finished_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Finalizada em"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criada em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizada em"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_campaigns",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criada por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Campanha de CRM",
                "verbose_name_plural": "Campanhas de CRM",
                "ordering": ["status", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CustomerTag",
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
                    "name",
                    models.CharField(max_length=80, unique=True, verbose_name="Nome"),
                ),
                (
                    "color",
                    models.CharField(blank=True, max_length=20, verbose_name="Cor CSS"),
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
                "verbose_name": "Tag de cliente",
                "verbose_name_plural": "Tags de cliente",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="CustomerInteraction",
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
                    "interaction_type",
                    models.CharField(
                        choices=[
                            ("call", "Ligação"),
                            ("whatsapp", "WhatsApp"),
                            ("email", "E-mail"),
                            ("visit", "Visita"),
                            ("service_order", "Ordem de serviço"),
                            ("post_sale", "Pós-venda"),
                            ("portal", "Portal do cliente"),
                            ("campaign", "Campanha"),
                            ("internal", "Interna"),
                        ],
                        max_length=30,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("phone", "Telefone"),
                            ("whatsapp", "WhatsApp"),
                            ("email", "E-mail"),
                            ("in_person", "Presencial"),
                            ("system", "Sistema"),
                            ("portal", "Portal"),
                            ("other", "Outro"),
                        ],
                        default="system",
                        max_length=30,
                        verbose_name="Canal",
                    ),
                ),
                ("subject", models.CharField(max_length=150, verbose_name="Assunto")),
                ("description", models.TextField(verbose_name="Descrição")),
                (
                    "interaction_date",
                    models.DateTimeField(verbose_name="Data da interação"),
                ),
                (
                    "next_follow_up_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Próximo follow-up"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criada em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizada em"),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crm_interactions",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "responsible_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_interactions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
                (
                    "service_order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_interactions",
                        to="service_orders.serviceorder",
                        verbose_name="Ordem de serviço",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_interactions",
                        to="customers.vehicle",
                        verbose_name="Veículo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Interação de CRM",
                "verbose_name_plural": "Interações de CRM",
                "ordering": ["-interaction_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CustomerOpportunity",
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
                ("title", models.CharField(max_length=150, verbose_name="Título")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "estimated_value",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Valor estimado",
                    ),
                ),
                (
                    "probability",
                    models.PositiveSmallIntegerField(
                        default=50, verbose_name="Probabilidade (%)"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Aberta"),
                            ("won", "Ganha"),
                            ("lost", "Perdida"),
                            ("canceled", "Cancelada"),
                        ],
                        default="open",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "expected_close_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Previsão de fechamento"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criada em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizada em"),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crm_opportunities",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "responsible_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_opportunities",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
                (
                    "service_order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_opportunities",
                        to="service_orders.serviceorder",
                        verbose_name="Ordem de serviço",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_opportunities",
                        to="customers.vehicle",
                        verbose_name="Veículo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Oportunidade de CRM",
                "verbose_name_plural": "Oportunidades de CRM",
                "ordering": ["status", "expected_close_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CustomerReminder",
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
                ("title", models.CharField(max_length=150, verbose_name="Título")),
                ("notes", models.TextField(blank=True, verbose_name="Observações")),
                ("due_date", models.DateField(verbose_name="Data de vencimento")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("done", "Concluído"),
                            ("canceled", "Cancelado"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crm_reminders",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "responsible_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_reminders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
                (
                    "service_order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_reminders",
                        to="service_orders.serviceorder",
                        verbose_name="Ordem de serviço",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="crm_reminders",
                        to="customers.vehicle",
                        verbose_name="Veículo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lembrete de CRM",
                "verbose_name_plural": "Lembretes de CRM",
                "ordering": ["status", "due_date", "customer__name"],
            },
        ),
        migrations.CreateModel(
            name="CampaignAudience",
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
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audience",
                        to="crm.campaign",
                        verbose_name="Campanha",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crm_campaign_audiences",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Público da campanha",
                "verbose_name_plural": "Público das campanhas",
                "unique_together": {("campaign", "customer")},
            },
        ),
        migrations.AddIndex(
            model_name="customerinteraction",
            index=models.Index(
                fields=["customer", "-interaction_date"],
                name="crm_custome_custome_74f7ca_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="customerinteraction",
            index=models.Index(
                fields=["service_order", "-interaction_date"],
                name="crm_custome_service_0a6c95_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="customerinteraction",
            index=models.Index(
                fields=["next_follow_up_date"], name="crm_custome_next_fo_2d885e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="customerreminder",
            index=models.Index(
                fields=["status", "due_date"], name="crm_custome_status_dcfbd4_idx"
            ),
        ),
    ]
