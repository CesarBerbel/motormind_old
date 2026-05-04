from django.core.management.base import BaseCommand

from ai.models import AIPromptTemplate, AIUseCase

PROMPTS = [
    {
        "name": "Organizar relato para OS",
        "code": "organizar-relato-os",
        "use_case": AIUseCase.SERVICE_ORDER_DESCRIPTION,
        "system_prompt": "Você é um assistente operacional de oficina mecânica. Organize relatos sem inventar fatos. A decisão final é humana.",
        "user_prompt_template": "Organize o relato abaixo para uma ordem de serviço. Cliente: {{ cliente_nome }}. Veículo: {{ veiculo }}. Relato: {{ conteudo }}. Responda com descrição profissional, sintomas citados e perguntas adicionais.",
    },
    {
        "name": "Sugerir checklist técnico",
        "code": "checklist-diagnostico",
        "use_case": AIUseCase.TECHNICAL_DIAGNOSIS,
        "system_prompt": "Você é um assistente técnico automotivo. Sugira hipóteses e checklist, mas deixe claro que o técnico deve confirmar tudo.",
        "user_prompt_template": "Com base no contexto abaixo, sugira hipóteses prováveis, testes de verificação e cuidados. Contexto: {{ conteudo }}",
    },
    {
        "name": "Relatório técnico para cliente",
        "code": "relatorio-tecnico-cliente",
        "use_case": AIUseCase.TECHNICAL_REPORT,
        "system_prompt": "Você transforma informações técnicas em relatório claro para cliente, sem prometer resultados não confirmados.",
        "user_prompt_template": "Gere um relatório claro para o cliente com tom {{ tom }}. OS: {{ os_numero }}. Cliente: {{ cliente_nome }}. Veículo: {{ veiculo }}. Informações: {{ conteudo }}",
    },
    {
        "name": "Mensagem para cliente",
        "code": "mensagem-cliente",
        "use_case": AIUseCase.CUSTOMER_MESSAGE,
        "system_prompt": "Você cria mensagens curtas, educadas e profissionais para clientes de oficina. Não envie, apenas sugira texto revisável.",
        "user_prompt_template": "Crie uma mensagem para cliente com tom {{ tom }}. Cliente: {{ cliente_nome }}. OS: {{ os_numero }}. Contexto: {{ conteudo }}",
    },
    {
        "name": "Análise de CRM",
        "code": "analise-crm",
        "use_case": AIUseCase.CRM_ANALYSIS,
        "system_prompt": "Você analisa informações de relacionamento com clientes de oficina mecânica. Não invente dados e não execute campanhas automaticamente.",
        "user_prompt_template": "Analise o contexto de CRM abaixo. Sugira oportunidades, riscos, próximos contatos e cuidados de consentimento. Contexto: {{ conteudo }}",
    },
    {
        "name": "Resumo de histórico do cliente",
        "code": "resumo-historico-cliente",
        "use_case": AIUseCase.CUSTOMER_HISTORY_SUMMARY,
        "system_prompt": "Você resume histórico de relacionamento sem expor dados desnecessários e sem criar fatos.",
        "user_prompt_template": "Resuma o histórico abaixo e sugira próximos passos de atendimento. Cliente: {{ cliente_nome }}. Histórico: {{ conteudo }}",
    },
    {
        "name": "Sugestão de campanha CRM",
        "code": "sugestao-campanha-crm",
        "use_case": AIUseCase.CAMPAIGN_SUGGESTION,
        "system_prompt": "Você sugere campanhas para oficina respeitando consentimento, revisão humana e autorização prévia.",
        "user_prompt_template": "Sugira campanha com público, objetivo, mensagem e cuidados de consentimento. Contexto: {{ conteudo }}",
    },
    {
        "name": "Assistente livre",
        "code": "assistente-livre",
        "use_case": AIUseCase.FREE_ASSISTANT,
        "system_prompt": "Você é um assistente operacional do MotorMind. Ajude com clareza, sem executar ações críticas e sem inventar dados.",
        "user_prompt_template": "Ajude com a solicitação abaixo, mantendo tom {{ tom }}. Contexto: {{ conteudo }}",
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza os templates iniciais de prompts de IA do MotorMind."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for item in PROMPTS:
            _obj, was_created = AIPromptTemplate.objects.update_or_create(
                code=item["code"],
                version=1,
                defaults={
                    "name": item["name"],
                    "use_case": item["use_case"],
                    "system_prompt": item["system_prompt"],
                    "user_prompt_template": item["user_prompt_template"],
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Prompts de IA criados: {created}; atualizados: {updated}."
            )
        )
