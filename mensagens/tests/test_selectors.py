import pytest
from django.utils import timezone

from mensagens.models import (
    MessageChannel,
    MessageLog,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
    MessageVariable,
)
from mensagens.selectors import (
    get_logs_for_list,
    get_message_dashboard_data,
    get_message_variables_for_help,
    get_queue_for_list,
    get_templates_for_list,
)


@pytest.mark.django_db
def test_get_message_dashboard_data_counts_queue_logs_and_templates(
    customer, attendant_user, email_template
):
    MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Pendente",
        body="Corpo",
        status=MessageStatus.PENDING,
        created_by=attendant_user,
    )
    MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Falha",
        body="Corpo",
        status=MessageStatus.FAILED,
        created_by=attendant_user,
    )
    MessageLog.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Enviada",
        body_snapshot="Corpo",
        status=MessageStatus.SENT,
        sent_at=timezone.now(),
        created_by=attendant_user,
    )

    data = get_message_dashboard_data()

    assert data["pending_count"] == 1
    assert data["failed_count"] == 1
    assert data["sent_today_count"] == 1
    assert data["active_templates_count"] == 1
    assert len(data["recent_logs"]) == 1


@pytest.mark.django_db
def test_get_templates_for_list_filters_by_search_and_channel(
    email_template, whatsapp_template
):
    result = list(
        get_templates_for_list(search="whatsapp", channel=MessageChannel.WHATSAPP)
    )

    assert result == [whatsapp_template]


@pytest.mark.django_db
def test_get_templates_for_list_searches_code(email_template, whatsapp_template):
    result = list(get_templates_for_list(search="teste_email"))

    assert result == [email_template]


@pytest.mark.django_db
def test_get_queue_for_list_filters_status_and_channel(customer):
    email_queue = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body="Email pendente",
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

    result = list(
        get_queue_for_list(status=MessageStatus.PENDING, channel=MessageChannel.EMAIL)
    )

    assert result == [email_queue]


@pytest.mark.django_db
def test_get_queue_for_list_orders_by_newest_first(customer):
    first = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body="Primeira",
    )
    second = MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body="Segunda",
    )

    result = list(get_queue_for_list())

    assert result[0] == second
    assert result[1] == first


@pytest.mark.django_db
def test_get_logs_for_list_filters_status_and_channel(customer):
    sent_log = MessageLog.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        body_snapshot="Enviada",
        status=MessageStatus.SENT,
    )
    MessageLog.objects.create(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.phone,
        body_snapshot="Falhou",
        status=MessageStatus.FAILED,
    )

    result = list(
        get_logs_for_list(status=MessageStatus.SENT, channel=MessageChannel.EMAIL)
    )

    assert result == [sent_log]


@pytest.mark.django_db
def test_get_message_variables_for_help_groups_registered_and_detects_uncatalogued(
    email_template,
):
    MessageVariable.objects.create(
        code="cliente_nome",
        label="Nome do cliente",
        category="Cliente",
        example_value="Maria",
    )

    data = get_message_variables_for_help()

    assert "Cliente" in data["grouped_variables"]
    assert data["grouped_variables"]["Cliente"][0].code == "cliente_nome"
    assert "os_numero" in data["uncatalogued_variables"]
    assert data["registered_count"] == 1
    assert data["uncatalogued_count"] == 1


@pytest.mark.django_db
def test_get_message_variables_for_help_ignores_inactive_variables(email_template):
    MessageVariable.objects.create(
        code="cliente_nome",
        label="Nome do cliente",
        category="Cliente",
        is_active=False,
    )

    data = get_message_variables_for_help()

    assert data["registered_count"] == 0
    assert "cliente_nome" in data["uncatalogued_variables"]


@pytest.mark.django_db
def test_get_message_variables_for_help_ignores_inactive_templates():
    MessageTemplate.objects.create(
        name="Template inativo",
        code="template_inativo_vars",
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Assunto",
        body="Corpo",
        available_variables=["variavel_inativa"],
        is_active=False,
    )

    data = get_message_variables_for_help()

    assert "variavel_inativa" not in data["uncatalogued_variables"]
