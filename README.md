MotorMind - Sistema de Gestão para Oficina Mecânica

📌 Visão Geral

MotorMind é um sistema completo de gestão para oficinas mecânicas desenvolvido com Django. O objetivo é controlar ordens de serviço, clientes, veículos, produtividade da equipe e operação diária da oficina com foco em rastreabilidade, controle e eficiência.

🧱 Arquitetura do Projeto

O projeto segue boas práticas do Django com separação clara de responsabilidades:

models → estrutura do banco

forms → validação de entrada

views → camada HTTP

selectors → consultas reutilizáveis

services → regras de negócio

permissions → controle de acesso

📦 Apps do Projeto

1. accounts

Responsável por autenticação e controle de usuários.

Funcionalidades

Login com email

Controle por grupos:

Administrador

Atendente

Mecânico

Financeiro

Permissões centralizadas (permissions.py)

Regras de negócio

Superusuário tem acesso total

Permissões não dependem diretamente de strings de grupo nas views

2. customers

Gerencia clientes e veículos.

Funcionalidades

Cadastro de clientes

Cadastro de veículos vinculados ao cliente

Listagem e busca

Regras

Veículo pertence a um único cliente

Veículos podem ser filtrados por cliente (AJAX)

3. service_orders (núcleo do sistema)

Controla toda a operação da oficina.

🧾 Ordem de Serviço (ServiceOrder)

Funcionalidades

Criação de OS

Edição administrativa

Atualização técnica (mecânico)

Cancelamento

Controle de status

Controle de prioridade

Controle de custos

Histórico de alterações

Status

OPEN

IN_PROGRESS

WAITING_PARTS

FINISHED

CANCELED

Prioridade

HIGH

MEDIUM

LOW

💰 Módulo Financeiro

Funcionalidades

Itens da OS

Subtotal

Desconto

Total

Máscara BRL (R$)

Regras

Valores validados no backend

Formatação no frontend com JS

Precisão monetária garantida

🧩 Itens da Ordem

Adicionar item

Editar item

Remover item

Cada item possui:

descrição

quantidade

preço unitário

📝 Notas Internas

Criadas por usuários

Não visíveis ao cliente

Histórico interno

🧠 Histórico (Audit Trail)

Funcionalidade

Toda alteração relevante gera histórico:

campo alterado

valor antigo

valor novo

usuário

data

Regras

Apenas campos auditados são registrados

Uso de bulk_create para performance

🧭 Quadro Operacional (Board)

Funcionalidades

Visualização por status

Drag and drop

Mudança rápida de status

Contadores dinâmicos

Destaque visual

Filtros

Mecânico

Prioridade

Atrasadas

Período de entrega

Busca textual

Regras

OS atrasada = data < hoje e não finalizada

⏱️ Controle de Tempo

Funcionalidades

Iniciar apontamento

Encerrar apontamento

Controle por mecânico

Regras

Mecânico não pode ter dois apontamentos abertos

Não pode apontar em OS cancelada

Admin pode encerrar qualquer apontamento

📊 Relatório de Produtividade

Funcionalidades

Tempo por mecânico

Tempo por OS

Filtro por período

Regras

Apenas apontamentos encerrados entram

📅 Agenda da Oficina

Funcionalidades

Visualização diária/semanal

Baseado em data de entrega

🔐 Permissões

Centralizadas em accounts/permissions.py

Benefícios

Evita duplicação

Facilita manutenção

Regras consistentes

🧠 Evolução Arquitetural

Fase 1 — CRUD básico

Models

Views simples

Fase 2 — Regras de negócio

Status

Financeiro

Histórico

Fase 3 — UX operacional

Quadro

Drag and drop

Filtros

Fase 4 — Camadas avançadas

selectors

services

permissions

Fase 5 — Refatoração

Views desacopladas

Lógica movida para services

🧪 Testes

Cobertura inclui:

views

forms

permissões

board

time tracking

relatórios

🚀 Próximos passos sugeridos

SLA automático por prioridade

Notificações

API REST

Multi-tenant

Dashboard financeiro avançado

📌 Conclusão

MotorMind evoluiu de um CRUD simples para uma arquitetura profissional baseada em:

separação de responsabilidades

regras de negócio centralizadas

alta rastreabilidade

foco operacional