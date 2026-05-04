import pytest
from django.core import mail
from django.utils import timezone

from core.exceptions import DomainError, ObjectNotFoundError, PermissionDeniedError
from mensagens.models import (
    MessageChannel,
    MessageLog,
    MessagePreference,
    MessageStatus,
    MessageType,
)
from mensagens.services import (
    create_log_from_queue,
    customer_allows_message,
    enqueue_from_template,
    enqueue_message,
    get_recipient_for_customer,
    process_pending_messages,
    process_queue_message,
    render_message_template,
    send_email_queue_message,
    send_whatsapp_queue_message,
)


@pytest.mark.django_db
def test_render_message_template_replaces_variables(email_template):
    subject, body = render_message_template(
        email_template,
        {"cliente_nome": "Maria", "os_numero": "OS-10"},
    )

    assert subject == "Olá Maria"
    assert body == "Mensagem para Maria sobre a OS OS-10."


@pytest.mark.django_db
def test_render_message_template_keeps_missing_variables_empty(email_template):
    subject, body = render_message_template(email_template, {"cliente_nome": "Maria"})

    assert subject == "Olá Maria"
    assert "OS" in body


@pytest.mark.django_db
def test_get_recipient_for_customer_returns_email_for_email_channel(customer):
    assert get_recipient_for_customer(customer, MessageChannel.EMAIL) == customer.email


@pytest.mark.django_db
def test_get_recipient_for_customer_returns_phone_for_whatsapp_channel(customer):
    assert (
        get_recipient_for_customer(customer, MessageChannel.WHATSAPP) == customer.phone
    )


@pytest.mark.django_db
def test_get_recipient_for_customer_requires_email(customer):
    customer.email = ""
    customer.save(update_fields=["email"])

    with pytest.raises(DomainError, match="e-mail"):
        get_recipient_for_customer(customer, MessageChannel.EMAIL)


@pytest.mark.django_db
def test_get_recipient_for_customer_requires_phone(customer):
    customer.phone = ""
    customer.save(update_fields=["phone"])

    with pytest.raises(DomainError, match="telefone"):
        get_recipient_for_customer(customer, MessageChannel.WHATSAPP)


@pytest.mark.django_db
def test_get_recipient_for_customer_rejects_invalid_channel(customer):
    with pytest.raises(DomainError, match="Canal"):
        get_recipient_for_customer(customer, "sms")


@pytest.mark.django_db
def test_transactional_message_is_allowed_without_explicit_preference(customer):
    assert (
        customer_allows_message(
            customer, MessageChannel.EMAIL, MessageType.TRANSACTIONAL
        )
        is True
    )
    assert (
        customer_allows_message(
            customer, MessageChannel.WHATSAPP, MessageType.TRANSACTIONAL
        )
        is True
    )


@pytest.mark.django_db
def test_marketing_message_is_blocked_without_explicit_preference(customer):
    assert (
        customer_allows_message(customer, MessageChannel.EMAIL, MessageType.MARKETING)
        is False
    )
    assert (
        customer_allows_message(
            customer, MessageChannel.WHATSAPP, MessageType.MARKETING
        )
        is False
    )


@pytest.mark.django_db
def test_marketing_message_respects_consent_by_channel(customer):
    MessagePreference.objects.create(
        customer=customer,
        accepts_email_marketing=True,
        accepts_whatsapp_marketing=False,
    )

    assert (
        customer_allows_message(customer, MessageChannel.EMAIL, MessageType.MARKETING)
        is True
    )
    assert (
        customer_allows_message(
            customer, MessageChannel.WHATSAPP, MessageType.MARKETING
        )
        is False
    )


@pytest.mark.django_db
def test_transactional_message_respects_consent_by_channel(customer):
    MessagePreference.objects.create(
        customer=customer,
        accepts_email_transactional=False,
        accepts_whatsapp_transactional=True,
    )

    assert (
        customer_allows_message(
            customer, MessageChannel.EMAIL, MessageType.TRANSACTIONAL
        )
        is False
    )
    assert (
        customer_allows_message(
            customer, MessageChannel.WHATSAPP, MessageType.TRANSACTIONAL
        )
        is True
    )


@pytest.mark.django_db
def test_enqueue_message_creates_pending_queue_message(customer, attendant_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Assunto",
        body="Corpo da mensagem",
        created_by=attendant_user,
    )

    assert queue_message.customer == customer
    assert queue_message.recipient == customer.email
    assert queue_message.status == MessageStatus.PENDING
    assert queue_message.created_by == attendant_user


@pytest.mark.django_db
def test_enqueue_message_accepts_explicit_recipient_without_customer(attendant_user):
    queue_message = enqueue_message(
        customer=None,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.MANUAL,
        recipient="externo@example.com",
        subject="Assunto",
        body="Corpo",
        created_by=attendant_user,
    )

    assert queue_message.customer is None
    assert queue_message.recipient == "externo@example.com"


@pytest.mark.django_db
def test_enqueue_message_blocks_user_without_send_permission(customer, plain_user):
    with pytest.raises(PermissionDeniedError):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            body="Corpo da mensagem",
            created_by=plain_user,
        )


@pytest.mark.django_db
def test_enqueue_message_can_ignore_permission_for_system_events(customer, plain_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        body="Corpo da mensagem",
        created_by=plain_user,
        ignore_permission=True,
    )

    assert queue_message.created_by == plain_user
    assert queue_message.status == MessageStatus.PENDING


@pytest.mark.django_db
def test_enqueue_message_blocks_marketing_without_consent(customer, attendant_user):
    with pytest.raises(DomainError, match="autorizou"):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.MARKETING,
            body="Campanha comercial",
            created_by=attendant_user,
        )


@pytest.mark.django_db
def test_enqueue_message_can_ignore_consent_for_operational_override(
    customer, attendant_user
):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.MARKETING,
        subject="Campanha",
        body="Campanha comercial",
        created_by=attendant_user,
        ignore_consent=True,
    )

    assert queue_message.status == MessageStatus.PENDING


@pytest.mark.django_db
def test_enqueue_message_requires_body(customer, attendant_user):
    with pytest.raises(DomainError, match="corpo"):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            subject="Assunto",
            body=" ",
            created_by=attendant_user,
        )


@pytest.mark.django_db
def test_enqueue_message_requires_recipient_when_no_customer(attendant_user):
    with pytest.raises(DomainError, match="destinatário"):
        enqueue_message(
            customer=None,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.MANUAL,
            subject="Assunto",
            body="Corpo",
            created_by=attendant_user,
        )


@pytest.mark.django_db
def test_enqueue_message_rejects_inactive_template(
    customer, inactive_email_template, attendant_user
):
    with pytest.raises(DomainError, match="inativo"):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            template=inactive_email_template,
            variables={},
            created_by=attendant_user,
        )


@pytest.mark.django_db
def test_enqueue_message_rejects_template_channel_mismatch(
    customer, email_template, attendant_user
):
    with pytest.raises(DomainError, match="canal"):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.WHATSAPP,
            message_type=MessageType.TRANSACTIONAL,
            template=email_template,
            variables={"cliente_nome": "Maria", "os_numero": "OS-1"},
            created_by=attendant_user,
        )


@pytest.mark.django_db
def test_enqueue_from_template_renders_template_and_links_related_object(
    customer, service_order, email_template, attendant_user
):
    queue_message = enqueue_from_template(
        template_code=email_template.code,
        customer=customer,
        variables={"cliente_nome": "Maria", "os_numero": "OS-10"},
        related_object=service_order,
        created_by=attendant_user,
    )

    assert queue_message.template == email_template
    assert queue_message.subject == "Olá Maria"
    assert "OS-10" in queue_message.body
    assert queue_message.related_object == service_order


@pytest.mark.django_db
def test_enqueue_from_template_requires_active_template(customer):
    with pytest.raises(ObjectNotFoundError):
        enqueue_from_template(
            template_code="codigo_inexistente", customer=customer, variables={}
        )


@pytest.mark.django_db
def test_create_log_from_queue_copies_snapshot_and_relationship(queued_email):
    queued_email.status = MessageStatus.SENT
    queued_email.sent_at = timezone.now()
    queued_email.save(update_fields=["status", "sent_at", "updated_at"])

    log = create_log_from_queue(
        queued_email,
        status=MessageStatus.SENT,
        provider="provedor",
        provider_message_id="abc123",
    )

    assert log.queue_message == queued_email
    assert log.body_snapshot == queued_email.body
    assert log.provider == "provedor"
    assert log.provider_message_id == "abc123"


@pytest.mark.django_db
def test_send_email_queue_message_uses_django_email_backend(queued_email):
    response = send_email_queue_message(queued_email)

    assert response["provider"] == "django-email"
    assert response["provider_message_id"] == f"email-{queued_email.pk}"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [queued_email.recipient]


@pytest.mark.django_db
def test_send_whatsapp_queue_message_returns_auditable_simulation(
    customer, attendant_user
):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        body="Mensagem WhatsApp",
        created_by=attendant_user,
    )

    response = send_whatsapp_queue_message(queue_message)

    assert response == {
        "provider": "whatsapp-simulado",
        "provider_message_id": f"whatsapp-{queue_message.pk}",
    }


@pytest.mark.django_db
def test_process_queue_message_sends_email_and_creates_log(customer, attendant_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Assunto",
        body="Corpo da mensagem",
        created_by=attendant_user,
    )

    processed_message = process_queue_message(queue_message)

    assert processed_message.status == MessageStatus.SENT
    assert processed_message.sent_at is not None
    assert processed_message.provider_response["provider"] == "django-email"
    assert len(mail.outbox) == 1
    assert MessageLog.objects.filter(
        queue_message=queue_message,
        status=MessageStatus.SENT,
        body_snapshot="Corpo da mensagem",
    ).exists()


@pytest.mark.django_db
def test_process_queue_message_sends_whatsapp_simulation(customer, attendant_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        body="Mensagem WhatsApp",
        created_by=attendant_user,
    )

    processed_message = process_queue_message(queue_message)

    assert processed_message.status == MessageStatus.SENT
    assert processed_message.provider_response["provider"] == "whatsapp-simulado"
    assert MessageLog.objects.filter(
        queue_message=queue_message, status=MessageStatus.SENT
    ).exists()


@pytest.mark.django_db
def test_process_queue_message_blocks_already_sent_message(customer, attendant_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        body="Mensagem WhatsApp",
        created_by=attendant_user,
    )
    queue_message.status = MessageStatus.SENT
    queue_message.sent_at = timezone.now()
    queue_message.save(update_fields=["status", "sent_at", "updated_at"])

    with pytest.raises(DomainError, match="pendentes"):
        process_queue_message(queue_message)


@pytest.mark.django_db
def test_process_queue_message_marks_failed_and_creates_log_when_provider_fails(
    monkeypatch, queued_email
):
    def fake_send_email(_queue_message):
        raise RuntimeError("provedor indisponível")

    monkeypatch.setattr("mensagens.services.send_email_queue_message", fake_send_email)

    with pytest.raises(RuntimeError, match="provedor indisponível"):
        process_queue_message(queued_email)

    queued_email.refresh_from_db()
    assert queued_email.status == MessageStatus.FAILED
    assert queued_email.retry_count == 1
    assert queued_email.failed_at is not None
    assert "provedor indisponível" in queued_email.error_message
    assert MessageLog.objects.filter(
        queue_message=queued_email, status=MessageStatus.FAILED
    ).exists()


@pytest.mark.django_db
def test_process_queue_message_reprocesses_failed_message(customer, attendant_user):
    queue_message = enqueue_message(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        body="Mensagem WhatsApp",
        created_by=attendant_user,
    )
    queue_message.status = MessageStatus.FAILED
    queue_message.error_message = "Falha anterior"
    queue_message.save(update_fields=["status", "error_message", "updated_at"])

    processed = process_queue_message(queue_message)

    assert processed.status == MessageStatus.SENT
    assert processed.error_message == ""


@pytest.mark.django_db
def test_process_pending_messages_respects_limit(customer, attendant_user):
    for index in range(3):
        enqueue_message(
            customer=customer,
            channel=MessageChannel.WHATSAPP,
            message_type=MessageType.TRANSACTIONAL,
            body=f"Mensagem {index}",
            created_by=attendant_user,
        )

    result = process_pending_messages(limit=2)

    assert result == {"processed": 2, "failed": 0}
    assert MessageLog.objects.filter(status=MessageStatus.SENT).count() == 2
    assert MessageLog.objects.filter(status=MessageStatus.SENT).count() == 2


@pytest.mark.django_db
def test_process_pending_messages_ignores_future_scheduled_messages(
    customer, attendant_user
):
    enqueue_message(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        body="Mensagem futura",
        scheduled_at=timezone.now() + timezone.timedelta(days=1),
        created_by=attendant_user,
    )

    result = process_pending_messages(limit=10)

    assert result == {"processed": 0, "failed": 0}


@pytest.mark.django_db
def test_process_pending_messages_counts_failures(
    monkeypatch, customer, attendant_user
):
    enqueue_message(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Assunto",
        body="Corpo",
        created_by=attendant_user,
    )

    def fake_process(_queue_message):
        raise RuntimeError("falhou")

    monkeypatch.setattr("mensagens.services.process_queue_message", fake_process)

    result = process_pending_messages(limit=10)

    assert result == {"processed": 0, "failed": 1}
