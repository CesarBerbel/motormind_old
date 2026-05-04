import pytest
from django.utils import timezone

from mensagens.forms import ManualMessageForm, MessageTemplateForm, QueueFilterForm
from mensagens.models import MessageChannel, MessageStatus, MessageType


@pytest.mark.django_db
def test_message_template_form_accepts_valid_json_variables():
    form = MessageTemplateForm(
        data={
            "name": "Template formulário",
            "code": "template_formulario",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "Assunto {{ cliente_nome }}",
            "body": "Corpo para {{ cliente_nome }}",
            "available_variables": '["cliente_nome"]',
            "is_active": "on",
        }
    )

    assert form.is_valid(), form.errors
    template = form.save()
    assert template.code == "template_formulario"
    assert template.available_variables == ["cliente_nome"]


@pytest.mark.django_db
def test_message_template_form_accepts_variables_by_line():
    form = MessageTemplateForm(
        data={
            "name": "Template linhas",
            "code": "template_linhas",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "",
            "body": "Olá {{ cliente_nome }}, OS {{ os_numero }}.",
            "available_variables": "cliente_nome\nos_numero",
            "is_active": "on",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["available_variables"] == ["cliente_nome", "os_numero"]


@pytest.mark.django_db
def test_message_template_form_accepts_variables_by_comma():
    form = MessageTemplateForm(
        data={
            "name": "Template vírgula",
            "code": "template_virgula",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.RELATIONSHIP,
            "subject": "",
            "body": "Olá {{ cliente_nome }} sobre {{ veiculo_identificacao }}.",
            "available_variables": "cliente_nome, veiculo_identificacao",
            "is_active": "on",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["available_variables"] == [
        "cliente_nome",
        "veiculo_identificacao",
    ]


@pytest.mark.django_db
def test_message_template_form_requires_email_subject():
    form = MessageTemplateForm(
        data={
            "name": "Template sem assunto",
            "code": "template_sem_assunto",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "",
            "body": "Corpo",
            "available_variables": "[]",
            "is_active": "on",
        }
    )

    assert not form.is_valid()
    assert "subject" in form.errors


@pytest.mark.django_db
def test_message_template_form_rejects_used_variable_not_registered():
    form = MessageTemplateForm(
        data={
            "name": "Template variável faltante",
            "code": "template_variavel_faltante",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "Assunto",
            "body": "Olá {{ cliente_nome }} e {{ os_numero }}",
            "available_variables": "cliente_nome",
            "is_active": "on",
        }
    )

    assert not form.is_valid()
    assert "available_variables" in form.errors
    assert "os_numero" in str(form.errors["available_variables"])


@pytest.mark.django_db
def test_message_template_form_normalizes_code_to_underscore():
    form = MessageTemplateForm(
        data={
            "name": "Template código",
            "code": "CODIGO-COM-HIFEN",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "",
            "body": "Corpo",
            "available_variables": "[]",
            "is_active": "on",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["code"] == "codigo_com_hifen"


@pytest.mark.django_db
def test_message_template_form_rejects_invalid_variable_name():
    form = MessageTemplateForm(
        data={
            "name": "Template inválido",
            "code": "template_invalido",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "subject": "",
            "body": "Corpo",
            "available_variables": "cliente-nome",
            "is_active": "on",
        }
    )

    assert not form.is_valid()
    assert "available_variables" in form.errors


@pytest.mark.django_db
def test_manual_message_form_accepts_minimum_valid_payload(customer):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": "",
            "subject": "Assunto",
            "body": "Corpo da mensagem",
            "variables": "",
            "scheduled_at": "",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["variables"] == {}


@pytest.mark.django_db
def test_manual_message_form_accepts_template_with_required_variables(
    customer, email_template
):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": email_template.pk,
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": "",
            "subject": "",
            "body": "",
            "variables": '{"cliente_nome": "Maria", "os_numero": "OS-1"}',
            "scheduled_at": "",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["variables"] == {
        "cliente_nome": "Maria",
        "os_numero": "OS-1",
    }


@pytest.mark.django_db
def test_manual_message_form_rejects_invalid_variables_json(customer):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.email,
            "subject": "Assunto",
            "body": "Corpo",
            "variables": "{json inválido}",
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "variables" in form.errors


@pytest.mark.django_db
def test_manual_message_form_rejects_template_channel_mismatch(
    customer, email_template
):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": email_template.pk,
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.phone,
            "subject": "",
            "body": "",
            "variables": '{"cliente_nome": "Maria", "os_numero": "OS-1"}',
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "channel" in form.errors


@pytest.mark.django_db
def test_manual_message_form_rejects_template_type_mismatch(customer, email_template):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": email_template.pk,
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.MARKETING,
            "recipient": customer.email,
            "subject": "",
            "body": "",
            "variables": '{"cliente_nome": "Maria", "os_numero": "OS-1"}',
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "message_type" in form.errors


@pytest.mark.django_db
def test_manual_message_form_rejects_missing_template_variables(
    customer, email_template
):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": email_template.pk,
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.email,
            "subject": "",
            "body": "",
            "variables": '{"cliente_nome": "Maria"}',
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "variables" in form.errors
    assert "os_numero" in str(form.errors["variables"])


@pytest.mark.django_db
def test_manual_message_form_requires_body_or_template(customer):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.phone,
            "subject": "",
            "body": "",
            "variables": "",
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "body" in form.errors


@pytest.mark.django_db
def test_manual_message_form_requires_subject_for_email_without_template(customer):
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.EMAIL,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.email,
            "subject": "",
            "body": "Corpo",
            "variables": "",
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "subject" in form.errors


@pytest.mark.django_db
def test_manual_message_form_requires_customer_or_recipient():
    form = ManualMessageForm(
        data={
            "customer": "",
            "template": "",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": "",
            "subject": "",
            "body": "Corpo",
            "variables": "",
            "scheduled_at": "",
        }
    )

    assert not form.is_valid()
    assert "recipient" in form.errors


@pytest.mark.django_db
def test_manual_message_form_accepts_scheduled_at(customer):
    scheduled_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")
    form = ManualMessageForm(
        data={
            "customer": customer.pk,
            "template": "",
            "channel": MessageChannel.WHATSAPP,
            "message_type": MessageType.TRANSACTIONAL,
            "recipient": customer.phone,
            "subject": "",
            "body": "Corpo",
            "variables": "",
            "scheduled_at": scheduled_at,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["scheduled_at"] is not None


@pytest.mark.django_db
def test_queue_filter_form_accepts_empty_filters():
    form = QueueFilterForm(data={})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["status"] == ""
    assert form.cleaned_data["channel"] == ""


@pytest.mark.django_db
def test_queue_filter_form_accepts_status_and_channel():
    form = QueueFilterForm(
        data={"status": MessageStatus.PENDING, "channel": MessageChannel.EMAIL}
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["status"] == MessageStatus.PENDING
    assert form.cleaned_data["channel"] == MessageChannel.EMAIL


@pytest.mark.django_db
def test_manual_message_template_queryset_only_active(
    email_template, inactive_email_template
):
    form = ManualMessageForm()

    assert email_template in form.fields["template"].queryset
    assert inactive_email_template not in form.fields["template"].queryset
