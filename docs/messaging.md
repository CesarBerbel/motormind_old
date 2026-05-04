# Arquitetura do módulo mensagens

## Objetivo

O app `mensagens` centraliza comunicação externa do MotorMind sem permitir que outros módulos escrevam diretamente nas tabelas de mensagens.

Outros módulos devem chamar somente serviços públicos, por exemplo:

- `enqueue_from_template(...)`
- `enqueue_service_order_opened_message(...)`
- `enqueue_vehicle_ready_message(...)`
- `enqueue_payment_received_message(...)`
- `enqueue_customer_portal_first_access_message(...)`

## Fronteiras do módulo

### models.py

Responsável por persistência:

- `MessageTemplate`: templates oficiais por canal e tipo.
- `MessageQueue`: fila auditável de mensagens pendentes/processadas.
- `MessageLog`: snapshot histórico do que foi enviado ou falhou.
- `MessageProvider`: configuração de provedores.
- `MessageEvent`: eventos de provedor/webhook.
- `MessageAttachment`: anexos vinculados à fila.
- `MessagePreference`: consentimento/preferência por cliente.
- `MessageVariable`: catálogo dinâmico de variáveis permitidas.

### services.py

Responsável por escrita e regras de negócio:

- valida permissão de envio;
- valida consentimento;
- renderiza template;
- resolve destinatário por cliente/canal;
- cria item na fila;
- processa envio;
- grava logs de sucesso/falha;
- expõe contratos públicos para OS, financeiro e portal.

### selectors.py

Responsável por leitura:

- dashboard;
- listagem de templates;
- listagem da fila;
- listagem de logs;
- página de ajuda de variáveis.

### forms.py e preview_forms.py

Responsáveis por validação de entrada das telas:

- cadastro/edição de templates;
- mensagem manual;
- filtros;
- preview de template com variáveis reais.

### template_renderer.py

Responsável por parsing e renderização segura do preview:

- extrai variáveis `{{ variavel }}`;
- aceita JSON ou `chave=valor`;
- preserva variáveis não preenchidas no preview;
- informa variáveis faltantes.

### views.py

Views finas. Não concentram regra de negócio. Devem chamar forms, selectors e services.

## Fluxo recomendado

1. Evento de negócio ocorre em outro módulo.
2. Módulo chama um serviço público de `mensagens`.
3. `mensagens` valida permissão/consentimento quando aplicável.
4. Template é renderizado.
5. Mensagem entra em `MessageQueue`.
6. Comando `process_messages` processa a fila.
7. Resultado é salvo em `MessageLog`.

## Comandos

```bash
python manage.py seed_message_templates
python manage.py seed_message_variables
python manage.py process_messages
```

## URLs

- `/mensagens/` dashboard
- `/mensagens/templates/` templates
- `/mensagens/variaveis/` ajuda de variáveis
- `/mensagens/preview/` preview renderizado
- `/mensagens/manual/nova/` mensagem manual
- `/mensagens/fila/` fila
- `/mensagens/logs/` logs

## Regras críticas

- Mensagem comercial exige consentimento explícito.
- Mensagem transacional é permitida por padrão quando não há preferência cadastrada.
- Corpo enviado deve ficar salvo como snapshot em `MessageLog`.
- Falha de provedor deve deixar a mensagem com status `failed` e criar log.
- Senhas/tokens devem ser marcados como variáveis sensíveis em `MessageVariable`.
