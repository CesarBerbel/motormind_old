from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import transaction
from django.template import Context, Template
from django.utils import timezone

from core.exceptions import DomainError, ObjectNotFoundError, PermissionDeniedError
from core.permissions import can_send_messages

from .models import (
    MessageChannel,
    MessageLog,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
)

SENSITIVE_VARIABLES = {"senha_inicial", "password", "token"}


def render_message_template(template, variables):
    safe_variables = variables or {}
    subject = Template(template.subject or "").render(Context(safe_variables))
    body = Template(template.body).render(Context(safe_variables))
    return subject.strip(), body.strip()


def get_recipient_for_customer(customer, channel):
    if channel == MessageChannel.EMAIL:
        if not customer.email:
            raise DomainError("O cliente não possui e-mail cadastrado.")
        return customer.email
    if channel == MessageChannel.WHATSAPP:
        if not customer.phone:
            raise DomainError("O cliente não possui telefone cadastrado.")
        return customer.phone
    raise DomainError("Canal de mensagem inválido.")


def customer_allows_message(customer, channel, message_type):
    preference = getattr(customer, "message_preference", None)
    if preference is None:
        return message_type != MessageType.MARKETING

    if message_type == MessageType.MARKETING:
        if channel == MessageChannel.EMAIL:
            return preference.accepts_email_marketing
        if channel == MessageChannel.WHATSAPP:
            return preference.accepts_whatsapp_marketing

    if channel == MessageChannel.EMAIL:
        return preference.accepts_email_transactional
    if channel == MessageChannel.WHATSAPP:
        return preference.accepts_whatsapp_transactional
    return False


@transaction.atomic
def enqueue_message(
    *,
    customer,
    channel,
    message_type,
    recipient=None,
    subject="",
    body="",
    template=None,
    variables=None,
    scheduled_at=None,
    related_object=None,
    created_by=None,
    ignore_consent=False,
    ignore_permission=False,
):
    if (
        created_by is not None
        and not ignore_permission
        and not can_send_messages(created_by)
    ):
        raise PermissionDeniedError("Você não tem permissão para enviar mensagens.")

    if customer is not None and not ignore_consent:
        if not customer_allows_message(customer, channel, message_type):
            raise DomainError(
                "O cliente não autorizou este tipo de mensagem neste canal."
            )

    if template is not None:
        if not template.is_active:
            raise DomainError("O template selecionado está inativo.")
        if template.channel != channel:
            raise DomainError("O canal do template não corresponde ao canal informado.")
        subject, body = render_message_template(template, variables or {})

    if not body.strip():
        raise DomainError("O corpo da mensagem é obrigatório.")

    if not recipient and customer is not None:
        recipient = get_recipient_for_customer(customer, channel)

    if not recipient:
        raise DomainError("O destinatário da mensagem é obrigatório.")

    content_type = None
    object_id = None
    if related_object is not None:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.pk

    return MessageQueue.objects.create(
        customer=customer,
        channel=channel,
        template=template,
        message_type=message_type,
        recipient=recipient,
        subject=subject,
        body=body,
        scheduled_at=scheduled_at or timezone.now(),
        related_content_type=content_type,
        related_object_id=object_id,
        created_by=created_by,
    )


def enqueue_from_template(
    *,
    template_code,
    customer,
    variables=None,
    scheduled_at=None,
    related_object=None,
    created_by=None,
    ignore_consent=False,
    ignore_permission=False,
):
    try:
        template = MessageTemplate.objects.get(code=template_code, is_active=True)
    except MessageTemplate.DoesNotExist as exc:
        raise ObjectNotFoundError(
            "Template de mensagem não encontrado ou inativo."
        ) from exc

    return enqueue_message(
        customer=customer,
        channel=template.channel,
        message_type=template.message_type,
        template=template,
        variables=variables or {},
        scheduled_at=scheduled_at,
        related_object=related_object,
        created_by=created_by,
        ignore_consent=ignore_consent,
        ignore_permission=ignore_permission,
    )


def create_log_from_queue(
    queue_message, *, status, provider="", provider_message_id="", error_message=""
):
    return MessageLog.objects.create(
        customer=queue_message.customer,
        queue_message=queue_message,
        channel=queue_message.channel,
        message_type=queue_message.message_type,
        recipient=queue_message.recipient,
        subject=queue_message.subject,
        body_snapshot=queue_message.body,
        status=status,
        sent_at=queue_message.sent_at,
        provider=provider,
        provider_message_id=provider_message_id,
        error_message=error_message,
        related_content_type=queue_message.related_content_type,
        related_object_id=queue_message.related_object_id,
        created_by=queue_message.created_by,
    )


def send_email_queue_message(queue_message):
    sent_count = send_mail(
        subject=queue_message.subject or "Mensagem MotorMind",
        message=queue_message.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[queue_message.recipient],
        fail_silently=False,
    )
    if sent_count != 1:
        raise DomainError("O provedor de e-mail não confirmou o envio.")
    return {
        "provider": "django-email",
        "provider_message_id": f"email-{queue_message.pk}",
    }


def send_whatsapp_queue_message(queue_message):
    # Integração real deve usar API oficial/provedor autorizado. Nesta fase, registramos simulação auditável.
    return {
        "provider": "whatsapp-simulado",
        "provider_message_id": f"whatsapp-{queue_message.pk}",
    }


def process_queue_message(queue_message):
    """
    Process one queued message with auditable state transitions.

    The provider call intentionally runs outside the database transaction that
    marks the message as PROCESSING. If the provider raises an exception, the
    FAILED status and log are committed before the exception is re-raised to the
    caller. This avoids transaction rollback returning the queue item to
    PENDING after a real provider failure.
    """
    with transaction.atomic():
        queue_message = MessageQueue.objects.select_for_update().get(
            pk=queue_message.pk
        )
        if queue_message.status not in [MessageStatus.PENDING, MessageStatus.FAILED]:
            raise DomainError(
                "Apenas mensagens pendentes ou com falha podem ser processadas."
            )

        queue_message.status = MessageStatus.PROCESSING
        queue_message.error_message = ""
        queue_message.save(update_fields=["status", "error_message", "updated_at"])

    try:
        if queue_message.channel == MessageChannel.EMAIL:
            response = send_email_queue_message(queue_message)
        elif queue_message.channel == MessageChannel.WHATSAPP:
            response = send_whatsapp_queue_message(queue_message)
        else:
            raise DomainError("Canal de mensagem não suportado.")
    except Exception as exc:
        with transaction.atomic():
            queue_message = MessageQueue.objects.select_for_update().get(
                pk=queue_message.pk
            )
            queue_message.status = MessageStatus.FAILED
            queue_message.failed_at = timezone.now()
            queue_message.retry_count += 1
            queue_message.error_message = str(exc)
            queue_message.save(
                update_fields=[
                    "status",
                    "failed_at",
                    "retry_count",
                    "error_message",
                    "updated_at",
                ]
            )
            create_log_from_queue(
                queue_message, status=MessageStatus.FAILED, error_message=str(exc)
            )
        raise

    with transaction.atomic():
        queue_message = MessageQueue.objects.select_for_update().get(
            pk=queue_message.pk
        )
        queue_message.status = MessageStatus.SENT
        queue_message.sent_at = timezone.now()
        queue_message.provider_response = response
        queue_message.save(
            update_fields=["status", "sent_at", "provider_response", "updated_at"]
        )
        create_log_from_queue(
            queue_message,
            status=MessageStatus.SENT,
            provider=response.get("provider", ""),
            provider_message_id=response.get("provider_message_id", ""),
        )
    return queue_message


def process_pending_messages(*, limit=50):
    now = timezone.now()
    messages = MessageQueue.objects.filter(
        status=MessageStatus.PENDING, scheduled_at__lte=now
    ).order_by("scheduled_at", "id")[:limit]
    processed = 0
    failed = 0
    for queue_message in messages:
        try:
            process_queue_message(queue_message)
            processed += 1
        except Exception:
            failed += 1
    return {"processed": processed, "failed": failed}


def get_workshop_name():
    """
    Return the public workshop name used in transactional templates.

    Keep this helper inside mensagens to avoid every module knowing how the
    company/system name is configured.
    """
    return getattr(settings, "MOTORMIND_WORKSHOP_NAME", "MotorMind")


def get_portal_url():
    """
    Return the customer portal URL used in first-access messages.
    """
    return getattr(settings, "MOTORMIND_PORTAL_URL", "http://127.0.0.1:8000/portal/")


def get_vehicle_identification(vehicle):
    """
    Format vehicle data consistently for customer-facing messages.
    """
    plate = getattr(vehicle, "plate", "") or "sem placa"
    brand = getattr(vehicle, "brand", "") or ""
    model = getattr(vehicle, "model", "") or ""
    description = f"{brand} {model}".strip()
    if description:
        return f"{plate} - {description}"
    return plate


def build_service_order_message_variables(service_order, extra_variables=None):
    """
    Build the standard variable payload used by OS-related templates.
    """
    customer = service_order.customer
    vehicle = service_order.vehicle
    variables = {
        "cliente_nome": customer.name,
        "cpf_cnpj": getattr(customer, "document", "")
        or getattr(customer, "cpf_cnpj", ""),
        "os_numero": getattr(service_order, "number", None) or service_order.pk,
        "veiculo_identificacao": get_vehicle_identification(vehicle),
        "portal_url": get_portal_url(),
        "nome_oficina": get_workshop_name(),
    }

    if extra_variables:
        variables.update(extra_variables)

    return variables


def enqueue_service_order_opened_message(service_order, *, created_by=None):
    """
    Queue the transactional message sent when a service order is opened.
    """
    return enqueue_from_template(
        template_code="abertura_os_email",
        customer=service_order.customer,
        variables=build_service_order_message_variables(service_order),
        related_object=service_order,
        created_by=created_by,
        ignore_permission=True,
    )


def enqueue_vehicle_ready_message(service_order, *, created_by=None):
    """
    Queue the transactional message sent when the vehicle is ready.
    """
    return enqueue_from_template(
        template_code="veiculo_pronto_whatsapp",
        customer=service_order.customer,
        variables=build_service_order_message_variables(service_order),
        related_object=service_order,
        created_by=created_by,
        ignore_permission=True,
    )


def enqueue_payment_received_message(payment, *, created_by=None):
    """
    Queue the transactional payment confirmation message.
    """
    receivable = payment.receivable
    service_order = receivable.service_order
    variables = build_service_order_message_variables(
        service_order,
        {
            "valor_total": str(receivable.final_amount),
            "valor_pago": str(payment.amount),
        },
    )

    return enqueue_from_template(
        template_code="pagamento_recebido_email",
        customer=receivable.customer,
        variables=variables,
        related_object=payment,
        created_by=created_by,
        ignore_permission=True,
    )


def enqueue_customer_portal_first_access_message(
    *,
    customer,
    service_order,
    initial_password,
    created_by=None,
):
    """
    Queue the first-access message for the customer portal.

    This service is intentionally public so the future portal_cliente/accounts
    workflow can create the customer user and then call mensagens without
    writing directly to message tables.
    """
    variables = build_service_order_message_variables(
        service_order,
        {"senha_inicial": initial_password},
    )

    return enqueue_from_template(
        template_code="primeiro_acesso_portal_email",
        customer=customer,
        variables=variables,
        related_object=service_order,
        created_by=created_by,
        ignore_permission=True,
    )
