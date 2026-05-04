# Generated manually for the MotorMind administrative workshop settings.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CompanySettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("name", models.CharField(max_length=150, verbose_name="Nome da oficina")),
                ("legal_name", models.CharField(blank=True, max_length=180, verbose_name="Razão social")),
                ("document", models.CharField(blank=True, max_length=20, verbose_name="CPF/CNPJ")),
                ("state_registration", models.CharField(blank=True, max_length=30, verbose_name="Inscrição estadual")),
                ("municipal_registration", models.CharField(blank=True, max_length=30, verbose_name="Inscrição municipal")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Telefone principal")),
                ("whatsapp", models.CharField(blank=True, max_length=30, verbose_name="WhatsApp")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Email principal")),
                ("website", models.URLField(blank=True, verbose_name="Site")),
                ("address_line", models.CharField(blank=True, max_length=180, verbose_name="Endereço")),
                ("number", models.CharField(blank=True, max_length=20, verbose_name="Número")),
                ("complement", models.CharField(blank=True, max_length=80, verbose_name="Complemento")),
                ("neighborhood", models.CharField(blank=True, max_length=100, verbose_name="Bairro")),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="Cidade")),
                ("state", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("zip_code", models.CharField(blank=True, max_length=12, verbose_name="CEP")),
                ("opening_hours", models.TextField(blank=True, verbose_name="Horário de funcionamento")),
                ("service_terms", models.TextField(blank=True, verbose_name="Termos de serviço e observações padrão")),
                ("is_configured", models.BooleanField(default=False, verbose_name="Configuração concluída")),
            ],
            options={
                "verbose_name": "Dados da oficina",
                "verbose_name_plural": "Dados da oficina",
            },
        ),
    ]
