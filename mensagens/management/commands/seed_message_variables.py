from django.core.management.base import BaseCommand

from mensagens.models import MessageVariable

DEFAULT_VARIABLES = [
    {
        "code": "cliente_nome",
        "label": "Nome do cliente",
        "description": "Nome completo do cliente.",
        "category": "Cliente",
        "example_value": "João Silva",
    },
    {
        "code": "cpf_cnpj",
        "label": "CPF/CNPJ",
        "description": "Documento do cliente.",
        "category": "Cliente",
        "example_value": "123.456.789-00",
        "is_sensitive": True,
    },
    {
        "code": "os_numero",
        "label": "Número da OS",
        "description": "Número da ordem de serviço.",
        "category": "Ordem de Serviço",
        "example_value": "OS-000123",
    },
    {
        "code": "veiculo_identificacao",
        "label": "Identificação do veículo",
        "description": "Placa, marca e modelo do veículo relacionado à mensagem.",
        "category": "Veículo",
        "example_value": "ABC1D23 - Volkswagen Gol",
    },
    {
        "code": "valor_total",
        "label": "Valor total",
        "description": "Valor total da OS, fatura ou cobrança.",
        "category": "Financeiro",
        "example_value": "R$ 850,00",
    },
    {
        "code": "valor_pago",
        "label": "Valor pago",
        "description": "Valor recebido em um pagamento.",
        "category": "Financeiro",
        "example_value": "R$ 300,00",
    },
    {
        "code": "portal_url",
        "label": "URL do portal",
        "description": "Endereço de acesso ao portal do cliente.",
        "category": "Portal",
        "example_value": "https://motormind.com.br/portal/",
    },
    {
        "code": "senha_inicial",
        "label": "Senha inicial",
        "description": "Senha temporária gerada para o primeiro acesso do cliente.",
        "category": "Portal",
        "example_value": "AbC123@xyz",
        "is_sensitive": True,
    },
    {
        "code": "data_retirada",
        "label": "Data de retirada",
        "description": "Data prevista ou confirmada para retirada do veículo.",
        "category": "Ordem de Serviço",
        "example_value": "15/05/2026",
    },
    {
        "code": "nome_oficina",
        "label": "Nome da oficina",
        "description": "Nome público da oficina que assina as mensagens.",
        "category": "Sistema",
        "example_value": "Oficina MotorMind",
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as variáveis padrão de mensagens."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for variable in DEFAULT_VARIABLES:
            _, created = MessageVariable.objects.update_or_create(
                code=variable["code"],
                defaults={
                    "label": variable["label"],
                    "description": variable["description"],
                    "category": variable["category"],
                    "example_value": variable["example_value"],
                    "is_sensitive": variable.get("is_sensitive", False),
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Variáveis processadas com sucesso. "
                f"Criadas: {created_count}. Atualizadas: {updated_count}."
            )
        )
