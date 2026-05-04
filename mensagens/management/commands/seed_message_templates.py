from django.core.management.base import BaseCommand

from mensagens.models import MessageChannel, MessageTemplate, MessageType

VARIABLES = [
    "cliente_nome",
    "cpf_cnpj",
    "os_numero",
    "veiculo_identificacao",
    "valor_total",
    "valor_pago",
    "portal_url",
    "senha_inicial",
    "data_retirada",
    "nome_oficina",
]

TEMPLATES = [
    {
        "name": "Abertura de OS",
        "code": "abertura_os_email",
        "channel": MessageChannel.EMAIL,
        "message_type": MessageType.TRANSACTIONAL,
        "subject": "Ordem de serviço {{ os_numero }} aberta",
        "body": (
            "Olá, {{ cliente_nome }}.\n\n"
            "Sua ordem de serviço nº {{ os_numero }} foi aberta para o veículo "
            "{{ veiculo_identificacao }}.\n\n"
            "A equipe da {{ nome_oficina }} avisará você sobre os próximos passos.\n\n"
            "Atenciosamente,\n"
            "{{ nome_oficina }}"
        ),
    },
    {
        "name": "Veículo pronto para retirada",
        "code": "veiculo_pronto_whatsapp",
        "channel": MessageChannel.WHATSAPP,
        "message_type": MessageType.TRANSACTIONAL,
        "subject": "",
        "body": (
            "Olá, {{ cliente_nome }}. Seu veículo {{ veiculo_identificacao }} "
            "está pronto para retirada. {{ nome_oficina }}"
        ),
    },
    {
        "name": "Pagamento recebido",
        "code": "pagamento_recebido_email",
        "channel": MessageChannel.EMAIL,
        "message_type": MessageType.TRANSACTIONAL,
        "subject": "Pagamento recebido - OS {{ os_numero }}",
        "body": (
            "Olá, {{ cliente_nome }}.\n\n"
            "Recebemos o pagamento de R$ {{ valor_pago }} referente à ordem de "
            "serviço nº {{ os_numero }}.\n\n"
            "Valor total da conta: R$ {{ valor_total }}.\n\n"
            "Obrigado,\n"
            "{{ nome_oficina }}"
        ),
    },
    {
        "name": "Primeiro acesso ao portal",
        "code": "primeiro_acesso_portal_email",
        "channel": MessageChannel.EMAIL,
        "message_type": MessageType.TRANSACTIONAL,
        "subject": "Acesso ao portal MotorMind",
        "body": (
            "Olá, {{ cliente_nome }}.\n\n"
            "Sua ordem de serviço nº {{ os_numero }} foi aprovada.\n"
            "Criamos um acesso ao portal MotorMind para você acompanhar o andamento "
            "do serviço.\n\n"
            "Login: {{ cpf_cnpj }}\n"
            "Senha inicial: {{ senha_inicial }}\n\n"
            "Por segurança, no primeiro acesso será obrigatório trocar essa senha "
            "por uma senha própria.\n\n"
            "Acesse: {{ portal_url }}"
        ),
    },
]


class Command(BaseCommand):
    help = "Cria templates iniciais do módulo de mensagens."

    def handle(self, *args, **options):
        for data in TEMPLATES:
            MessageTemplate.objects.update_or_create(
                code=data["code"],
                defaults={**data, "available_variables": VARIABLES},
            )
        self.stdout.write(
            self.style.SUCCESS("Templates de mensagem criados/atualizados.")
        )
