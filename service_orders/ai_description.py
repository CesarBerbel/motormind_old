import re

from ai.models import AIPromptTemplate, AIUseCase
from ai.services import generate_ai_response
from core.exceptions import DomainError

PROMPT_CODE = "improve_service_order_problem_description"

SYSTEM_PROMPT = """
Você é um assistente operacional de uma oficina mecânica.
Sua função é melhorar a descrição inicial do problema relatado pelo cliente,
sem inventar diagnóstico técnico, causa provável, peça defeituosa, orçamento,
prazo ou serviço executado.

Regras obrigatórias:
- Preserve fielmente os fatos informados.
- Não acrescente informações que o cliente não relatou.
- Não dê diagnóstico conclusivo.
- Não indique valores, peças ou prazos.
- Escreva em português do Brasil.
- Use tom profissional, claro, objetivo e adequado para uma ordem de serviço.
- Retorne apenas o texto melhorado, sem títulos, explicações ou listas extras.
""".strip()

USER_PROMPT_TEMPLATE = """
Melhore a descrição do problema abaixo para registro em uma ordem de serviço.

Descrição original:
{{ descricao }}
""".strip()

TEMPORARY_PROVIDER_ERROR_MARKERS = (
    "503",
    "unavailable",
    "high demand",
    "alta demanda",
    "temporarily unavailable",
    "try again later",
)


def get_or_create_problem_description_prompt():
    """Return the active prompt used by the OS opening form."""
    prompt, _created = AIPromptTemplate.objects.update_or_create(
        code=PROMPT_CODE,
        version=1,
        defaults={
            "name": "Melhorar descrição do problema da OS",
            "use_case": AIUseCase.SERVICE_ORDER_DESCRIPTION,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt_template": USER_PROMPT_TEMPLATE,
            "is_active": True,
        },
    )
    return prompt


def is_temporary_provider_error(error):
    """Return True when the AI provider failed because of temporary overload."""
    error_message = str(error).lower()
    return any(marker in error_message for marker in TEMPORARY_PROVIDER_ERROR_MARKERS)


def improve_problem_description_locally(description):
    """
    Fallback deterministic and safe when the external AI provider is unavailable.

    It only normalizes spacing, punctuation and capitalization. It does not add
    diagnosis, parts, values, dates, services or facts not provided by the user.
    """
    text = re.sub(r"\s+", " ", description.strip())
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", text)

    if not text:
        return ""

    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text = f"{text}."

    return text


def improve_problem_description(*, user, description):
    """Generate an improved service-order problem description."""
    prompt = get_or_create_problem_description_prompt()
    try:
        response = generate_ai_response(
            user=user,
            use_case=AIUseCase.SERVICE_ORDER_DESCRIPTION,
            input_data={"descricao": description.strip()},
            prompt_template=prompt,
        )
    except DomainError as error:
        if is_temporary_provider_error(error):
            return improve_problem_description_locally(description)
        raise

    return response.output_text.strip()
