import pytest
from django.core.management import call_command

from mensagens.management.commands.seed_message_templates import TEMPLATES
from mensagens.management.commands.seed_message_variables import DEFAULT_VARIABLES
from mensagens.models import (
    MessageChannel,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
    MessageVariable,
)


@pytest.mark.django_db
def test_seed_message_templates_command_is_idempotent():
    call_command("seed_message_templates")
    call_command("seed_message_templates")

    assert MessageTemplate.objects.count() == len(TEMPLATES)
    assert MessageTemplate.objects.filter(code="abertura_os_email").exists()
    assert MessageTemplate.objects.filter(code="primeiro_acesso_portal_email").exists()


@pytest.mark.django_db
def test_seed_message_templates_updates_existing_template():
    MessageTemplate.objects.create(
        name="Nome antigo",
        code="abertura_os_email",
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Antigo",
        body="Antigo",
    )

    call_command("seed_message_templates")

    template = MessageTemplate.objects.get(code="abertura_os_email")
    assert template.name == "Abertura de OS"
    assert template.subject == "Ordem de serviço {{ os_numero }} aberta"


@pytest.mark.django_db
def test_seed_message_variables_command_is_idempotent():
    call_command("seed_message_variables")
    call_command("seed_message_variables")

    assert MessageVariable.objects.count() == len(DEFAULT_VARIABLES)
    assert MessageVariable.objects.filter(
        code="cliente_nome", category="Cliente"
    ).exists()
    assert MessageVariable.objects.filter(
        code="senha_inicial", is_sensitive=True
    ).exists()


@pytest.mark.django_db
def test_seed_message_variables_updates_existing_variable():
    MessageVariable.objects.create(
        code="cliente_nome",
        label="Antigo",
        category="Antiga",
    )

    call_command("seed_message_variables")

    variable = MessageVariable.objects.get(code="cliente_nome")
    assert variable.label == "Nome do cliente"
    assert variable.category == "Cliente"


@pytest.mark.django_db
def test_process_messages_command_processes_pending_queue(customer, attendant_user):
    MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.phone,
        body="Mensagem pendente",
        created_by=attendant_user,
    )

    call_command("process_messages", limit=10)

    assert MessageQueue.objects.filter(status=MessageStatus.SENT).count() == 1


@pytest.mark.django_db
def test_process_messages_command_respects_limit(customer, attendant_user):
    for index in range(3):
        MessageQueue.objects.create(
            customer=customer,
            channel=MessageChannel.WHATSAPP,
            message_type=MessageType.TRANSACTIONAL,
            recipient=customer.phone,
            body=f"Mensagem {index}",
            created_by=attendant_user,
        )

    call_command("process_messages", limit=2)

    assert MessageQueue.objects.filter(status=MessageStatus.SENT).count() == 2
    assert MessageQueue.objects.filter(status=MessageStatus.PENDING).count() == 1
