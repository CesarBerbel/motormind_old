import pytest
from django.urls import reverse

from mensagens.models import (
    MessageChannel,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
    MessageVariable,
)


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("mensagens:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_dashboard_requires_message_view_permission(client, mechanic_user):
    client.force_login(mechanic_user)

    response = client.get(reverse("mensagens:dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:dashboard")


@pytest.mark.django_db
def test_dashboard_allows_admin(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("mensagens:dashboard"))

    assert response.status_code == 200
    assert "Mensagens" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_allows_attendant(client, attendant_user):
    client.force_login(attendant_user)

    response = client.get(reverse("mensagens:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_allows_financial(client, financial_user):
    client.force_login(financial_user)

    response = client.get(reverse("mensagens:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_template_list_allows_admin_and_filters(
    client, admin_user, email_template, whatsapp_template
):
    client.force_login(admin_user)

    response = client.get(
        reverse("mensagens:template_list"),
        {"q": "whatsapp", "channel": MessageChannel.WHATSAPP},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert whatsapp_template.name in content
    assert email_template.name not in content


@pytest.mark.django_db
def test_template_create_allows_admin(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("mensagens:template_create"),
        {
            "name": "Template via view",
            "code": "template_view",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "Assunto",
            "body": "Corpo",
            "available_variables": "[]",
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("mensagens:template_list")
    assert MessageTemplate.objects.filter(code="template_view").exists()


@pytest.mark.django_db
def test_template_create_rerenders_invalid_form(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("mensagens:template_create"),
        {
            "name": "Template inválido",
            "code": "template_invalido",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "",
            "body": "Corpo",
            "available_variables": "[]",
            "is_active": "on",
        },
    )

    assert response.status_code == 200
    assert not MessageTemplate.objects.filter(code="template_invalido").exists()


@pytest.mark.django_db
def test_template_create_blocks_attendant(client, attendant_user):
    client.force_login(attendant_user)

    response = client.get(reverse("mensagens:template_create"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:dashboard")


@pytest.mark.django_db
def test_template_update_allows_admin(client, admin_user, email_template):
    client.force_login(admin_user)

    response = client.post(
        reverse("mensagens:template_update", kwargs={"pk": email_template.pk}),
        {
            "name": "Template atualizado",
            "code": email_template.code,
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "Assunto atualizado",
            "body": "Corpo atualizado",
            "available_variables": "[]",
            "is_active": "on",
        },
    )

    email_template.refresh_from_db()
    assert response.status_code == 302
    assert email_template.name == "Template atualizado"
    assert email_template.subject == "Assunto atualizado"


@pytest.mark.django_db
def test_variable_help_page_lists_registered_and_uncatalogued_variables(
    client, admin_user, email_template
):
    MessageVariable.objects.create(
        code="cliente_nome",
        label="Nome do cliente",
        category="Cliente",
    )
    client.force_login(admin_user)

    response = client.get(reverse("mensagens:variable_help"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Variáveis disponíveis" in content
    assert "cliente_nome" in content
    assert "os_numero" in content


@pytest.mark.django_db
def test_manual_message_create_enqueues_message(client, attendant_user, customer):
    client.force_login(attendant_user)

    response = client.post(
        reverse("mensagens:manual_message_create"),
        {
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": "",
            "subject": "Assunto manual",
            "body": "Mensagem manual",
            "variables": "",
            "scheduled_at": "",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("mensagens:queue_list")
    assert MessageQueue.objects.filter(
        customer=customer,
        subject="Assunto manual",
        body="Mensagem manual",
    ).exists()


@pytest.mark.django_db
def test_manual_message_create_rerenders_domain_error(client, attendant_user, customer):
    client.force_login(attendant_user)

    response = client.post(
        reverse("mensagens:manual_message_create"),
        {
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.MARKETING,
            "recipient": "",
            "subject": "Campanha",
            "body": "Mensagem comercial",
            "variables": "",
            "scheduled_at": "",
        },
    )

    assert response.status_code == 200
    assert MessageQueue.objects.count() == 0


@pytest.mark.django_db
def test_queue_list_filters_results(client, admin_user, customer):
    email_queue = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Email filtrado",
        body="Corpo",
        status=MessageStatus.PENDING,
    )
    MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.phone,
        body="WhatsApp enviado",
        status=MessageStatus.SENT,
    )
    client.force_login(admin_user)

    response = client.get(
        reverse("mensagens:queue_list"),
        {"status": MessageStatus.PENDING, "channel": MessageChannel.EMAIL},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert email_queue.subject in content
    assert "WhatsApp enviado" not in content


@pytest.mark.django_db
def test_queue_process_sends_message(client, attendant_user, customer):
    queue_message = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.phone,
        body="Mensagem para processar",
        created_by=attendant_user,
    )
    client.force_login(attendant_user)

    response = client.post(
        reverse("mensagens:queue_process", kwargs={"pk": queue_message.pk})
    )

    queue_message.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("mensagens:queue_list")
    assert queue_message.status == MessageStatus.SENT


@pytest.mark.django_db
def test_queue_process_handles_processing_failure(client, attendant_user, customer):
    queue_message = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body="Mensagem sem assunto",
        status=MessageStatus.SENT,
        created_by=attendant_user,
    )
    client.force_login(attendant_user)

    response = client.post(
        reverse("mensagens:queue_process", kwargs={"pk": queue_message.pk})
    )

    assert response.status_code == 302
    assert response.url == reverse("mensagens:queue_list")


@pytest.mark.django_db
def test_log_list_allows_financial(client, financial_user, sent_log):
    client.force_login(financial_user)

    response = client.get(
        reverse("mensagens:log_list"),
        {"status": MessageStatus.SENT, "channel": MessageChannel.EMAIL},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert sent_log.subject in content
