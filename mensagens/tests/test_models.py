import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from mensagens.models import (
    MessageAttachment,
    MessageChannel,
    MessageEvent,
    MessagePreference,
    MessageProvider,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
    MessageVariable,
)


@pytest.mark.django_db
def test_message_provider_string_representation():
    provider = MessageProvider.objects.create(
        name="SMTP Principal",
        channel=MessageChannel.EMAIL,
    )

    assert str(provider) == "SMTP Principal (E-mail)"


@pytest.mark.django_db
def test_message_template_code_is_unique(email_template):
    with pytest.raises(IntegrityError):
        MessageTemplate.objects.create(
            name="Duplicado",
            code=email_template.code,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            subject="Assunto",
            body="Corpo",
        )


@pytest.mark.django_db
def test_message_template_string_representation(email_template):
    assert str(email_template) == "Template de teste por e-mail (E-mail)"


@pytest.mark.django_db
def test_message_variable_placeholder_and_string_representation():
    variable = MessageVariable.objects.create(
        code="cliente_nome",
        label="Nome do cliente",
        description="Nome público do cliente.",
        category="Cliente",
        example_value="João Silva",
    )

    assert variable.placeholder == "{{ cliente_nome }}"
    assert str(variable) == "{{ cliente_nome }} - Nome do cliente"


@pytest.mark.django_db
def test_message_variable_code_is_unique():
    MessageVariable.objects.create(code="os_numero", label="Número da OS")

    with pytest.raises(IntegrityError):
        MessageVariable.objects.create(code="os_numero", label="Duplicada")


@pytest.mark.django_db
def test_message_preference_defaults_are_safe_for_marketing(customer):
    preference = MessagePreference.objects.create(customer=customer)

    assert preference.accepts_email_transactional is True
    assert preference.accepts_whatsapp_transactional is True
    assert preference.accepts_email_marketing is False
    assert preference.accepts_whatsapp_marketing is False
    assert preference.preferred_channel == MessageChannel.WHATSAPP
    assert str(preference) == f"Preferências de {customer}"


@pytest.mark.django_db
def test_message_queue_defaults(customer):
    queue_message = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.phone,
        body="Mensagem de teste",
    )

    assert queue_message.status == MessageStatus.PENDING
    assert queue_message.retry_count == 0
    assert queue_message.provider_response == {}
    assert queue_message.scheduled_at is not None
    assert "WhatsApp para" in str(queue_message)


@pytest.mark.django_db
def test_message_queue_negative_retry_count_is_invalid(customer):
    queue_message = MessageQueue(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body="Corpo",
        retry_count=-1,
    )

    with pytest.raises(ValidationError):
        queue_message.full_clean()


@pytest.mark.django_db
def test_message_log_keeps_snapshot_and_provider(sent_log):
    assert sent_log.body_snapshot == "Corpo enviado"
    assert sent_log.provider == "django-email"
    assert sent_log.provider_message_id == "email-1"
    assert "E-mail para" in str(sent_log)


@pytest.mark.django_db
def test_message_event_defaults_to_current_time(sent_log):
    event = MessageEvent.objects.create(
        log=sent_log,
        event_type="delivered",
        payload={"provider_status": "ok"},
    )

    assert event.occurred_at <= timezone.now()
    assert event.payload["provider_status"] == "ok"
    assert "delivered" in str(event)


@pytest.mark.django_db
def test_message_attachment_metadata_is_persisted(queued_email, uploaded_attachment):
    attachment = MessageAttachment.objects.create(
        queue_message=queued_email,
        file=uploaded_attachment,
        original_name="orcamento.pdf",
        content_type="application/pdf",
        size_bytes=123,
    )

    assert attachment.original_name == "orcamento.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.size_bytes == 123
    assert str(attachment) == "orcamento.pdf"
