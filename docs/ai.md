# Inteligência Artificial - MotorMind

O módulo `ai` fornece assistência operacional, técnica, comercial e textual para o MotorMind.

## Princípios

- A IA sugere, resume, organiza e redige.
- A IA não executa ações críticas automaticamente.
- Toda requisição, resposta, uso e revisão ficam registrados.
- Prompts são versionados em banco.
- Respostas são editáveis e revisáveis por humano.

## Casos de uso iniciais

- Organização de relato para ordem de serviço.
- Sugestão de checklist técnico.
- Relatório técnico para cliente.
- Mensagem para cliente.
- Análise de CRM.
- Resumo de histórico do cliente.
- Sugestão de campanha CRM.
- Assistente livre.

## Configuração local

Por padrão, `AI_PROVIDER=local` usa um provedor seguro de desenvolvimento que não chama API externa.

Para usar Google Gemini:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=sua-chave-gemini
GEMINI_MODEL=gemini-2.5-flash
AI_TEMPERATURE=0.2
```

Instale dependências e execute:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_ai_prompts
python manage.py runserver
```

Acesse `/ia/`.

## Observações de segurança

- A chave `GEMINI_API_KEY` nunca deve ser commitada no repositório.
- Use `.env` local ou variáveis de ambiente do servidor.
- A resposta do Gemini continua passando pela camada de revisão humana do módulo `ai`.
- O provider local pode ser usado em desenvolvimento quando não houver internet ou chave configurada.


## SDK Gemini

Este projeto usa o SDK atual do Google Gemini: `google-genai`.

Instale com:

```bash
pip install -U google-genai
```
