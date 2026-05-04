from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.template import Context, Template

from auditoria.services import log_event
from core.exceptions import DomainError, ObjectNotFoundError, PermissionDeniedError

from .models import (
    AIPromptTemplate,
    AIRequest,
    AIRequestStatus,
    AIResponse,
    AIReview,
    AIReviewStatus,
    AIUsageLog,
)
from .permissions import can_review_ai_output, can_use_ai_case
from .providers import AIProviderError, get_ai_provider

CRITICAL_ACTION_WARNING = (
    "A IA é apenas assistente. Revise e confirme manualmente antes de alterar OS, "
    "aprovar orçamento, movimentar estoque, registrar pagamento ou enviar campanha."
)


def render_prompt(template, input_data):
    safe_data = input_data or {}
    return Template(template.user_prompt_template).render(Context(safe_data)).strip()


def get_active_prompt_template(use_case, code=None):
    queryset = AIPromptTemplate.objects.filter(use_case=use_case, is_active=True)
    if code:
        queryset = queryset.filter(code=code)
    template = queryset.order_by("code", "-version").first()
    if template is None:
        raise ObjectNotFoundError(
            "Nenhum template de prompt ativo foi encontrado para este caso de uso."
        )
    return template


def _get_related_metadata(related_object):
    if related_object is None:
        return None, None
    return ContentType.objects.get_for_model(related_object), related_object.pk


@transaction.atomic
def create_ai_request(
    *,
    user,
    use_case,
    input_data,
    prompt_template=None,
    prompt_code=None,
    related_object=None,
):
    if not can_use_ai_case(user, use_case):
        raise PermissionDeniedError(
            "Você não tem permissão para usar IA neste recurso."
        )

    prompt_template = prompt_template or get_active_prompt_template(
        use_case, code=prompt_code
    )
    rendered_prompt = render_prompt(prompt_template, input_data)
    if not rendered_prompt:
        raise DomainError(
            "O prompt renderizado ficou vazio. Verifique os dados informados."
        )

    content_type, object_id = _get_related_metadata(related_object)
    request = AIRequest.objects.create(
        user=user,
        prompt_template=prompt_template,
        use_case=use_case,
        input_data=input_data or {},
        rendered_prompt=rendered_prompt,
        related_content_type=content_type,
        related_object_id=object_id,
    )
    AIUsageLog.objects.create(
        user=user,
        feature=prompt_template.code,
        use_case=use_case,
        status=AIRequestStatus.PENDING,
        related_content_type=content_type,
        related_object_id=object_id,
        metadata={"request_id": request.pk},
    )
    log_event(
        action="ai.request.created",
        user=user,
        obj=request,
        new_data={"use_case": use_case, "prompt_code": prompt_template.code},
    )
    return request


@transaction.atomic
def execute_ai_request(ai_request, *, provider=None):
    ai_request.status = AIRequestStatus.PROCESSING
    ai_request.error_message = ""
    ai_request.save(update_fields=["status", "error_message", "updated_at"])

    provider = provider or get_ai_provider()
    try:
        result = provider.generate(
            system_prompt=ai_request.prompt_template.system_prompt,
            user_prompt=ai_request.rendered_prompt,
        )
    except AIProviderError as exc:
        ai_request.status = AIRequestStatus.FAILED
        ai_request.error_message = str(exc)
        ai_request.save(update_fields=["status", "error_message", "updated_at"])
        AIUsageLog.objects.create(
            user=ai_request.user,
            feature=ai_request.prompt_template.code,
            use_case=ai_request.use_case,
            status=AIRequestStatus.FAILED,
            related_content_type=ai_request.related_content_type,
            related_object_id=ai_request.related_object_id,
            metadata={"request_id": ai_request.pk, "error": str(exc)},
        )
        log_event(
            action="ai.request.failed",
            user=ai_request.user,
            obj=ai_request,
            new_data={"error": str(exc)},
        )
        raise DomainError(f"Falha ao gerar resposta de IA: {exc}") from exc

    response = AIResponse.objects.create(
        request=ai_request,
        output_text=result.output_text,
        model_name=result.model_name,
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
        latency_ms=result.latency_ms,
        raw_response=result.raw_response or {},
    )
    ai_request.status = AIRequestStatus.COMPLETED
    ai_request.save(update_fields=["status", "updated_at"])
    AIUsageLog.objects.create(
        user=ai_request.user,
        feature=ai_request.prompt_template.code,
        use_case=ai_request.use_case,
        status=AIRequestStatus.COMPLETED,
        related_content_type=ai_request.related_content_type,
        related_object_id=ai_request.related_object_id,
        metadata={
            "request_id": ai_request.pk,
            "response_id": response.pk,
            "model_name": response.model_name,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
        },
    )
    log_event(
        action="ai.response.generated",
        user=ai_request.user,
        obj=response,
        new_data={"request_id": ai_request.pk, "model_name": response.model_name},
    )
    return response


@transaction.atomic
def generate_ai_response(
    *,
    user,
    use_case,
    input_data,
    prompt_template=None,
    prompt_code=None,
    related_object=None,
):
    ai_request = create_ai_request(
        user=user,
        use_case=use_case,
        input_data=input_data,
        prompt_template=prompt_template,
        prompt_code=prompt_code,
        related_object=related_object,
    )
    return execute_ai_request(ai_request)


@transaction.atomic
def review_ai_response(
    *, response, reviewed_by, status, edited_output_text="", notes=""
):
    if not can_review_ai_output(reviewed_by):
        raise PermissionDeniedError(
            "Você não tem permissão para revisar respostas de IA."
        )

    if status == AIReviewStatus.EDITED and not edited_output_text.strip():
        raise DomainError("Informe o texto editado ao marcar a revisão como editada.")

    review, _created = AIReview.objects.update_or_create(
        response=response,
        defaults={
            "reviewed_by": reviewed_by,
            "status": status,
            "edited_output_text": edited_output_text,
            "notes": notes,
        },
    )
    log_event(
        action="ai.response.reviewed",
        user=reviewed_by,
        obj=response,
        new_data={"status": status, "review_id": review.pk},
    )
    return review
