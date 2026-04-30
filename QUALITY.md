# Política de Qualidade do Projeto

## Objetivo

Garantir que o sistema da oficina seja seguro, testável, organizado e sustentável.

## Regras obrigatórias

Antes de qualquer nova funcionalidade, devem passar:

```bash
python manage.py check
ruff check .
ruff format --check .
pytest