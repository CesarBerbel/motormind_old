from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from core.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    MECHANIC_GROUP,
)
from customers.models import Customer, Vehicle
from financial.models import Payment, PaymentMethod, Receivable
from mensagens.models import (
    MessageChannel,
    MessageLog,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageType,
)
from service_orders.models import ServiceOrder


@pytest.fixture
def user_factory():
    def make_user(email, group_name=None, *, is_superuser=False):
        User = get_user_model()
        if is_superuser:
            user = User.objects.create_superuser(
                email=email,
                password="StrongPassword123",
            )
        else:
            user = User.objects.create_user(
                email=email,
                password="StrongPassword123",
            )
        if group_name:
            group, _created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user

    return make_user


@pytest.fixture
def admin_user(user_factory):
    return user_factory("mensagens_admin@example.com", ADMIN_GROUP)


@pytest.fixture
def attendant_user(user_factory):
    return user_factory("mensagens_attendant@example.com", ATTENDANT_GROUP)


@pytest.fixture
def financial_user(user_factory):
    return user_factory("mensagens_financial@example.com", FINANCIAL_GROUP)


@pytest.fixture
def mechanic_user(user_factory):
    return user_factory("mensagens_mechanic@example.com", MECHANIC_GROUP)


@pytest.fixture
def plain_user(user_factory):
    return user_factory("mensagens_plain@example.com")


@pytest.fixture
def superuser(user_factory):
    return user_factory("mensagens_superuser@example.com", is_superuser=True)


@pytest.fixture
def customer():
    return Customer.objects.create(
        name="Cliente Mensagens",
        phone="11999999999",
        email="cliente@example.com",
        document="12345678909",
    )


@pytest.fixture
def customer_without_contact():
    return Customer.objects.create(
        name="Cliente Sem Contato",
        phone="",
        email="",
        document="98765432100",
    )


@pytest.fixture
def vehicle(customer):
    return Vehicle.objects.create(
        customer=customer,
        plate="MSG-0001",
        brand="Volkswagen",
        model="Gol",
    )


@pytest.fixture
def service_order(customer, vehicle, admin_user):
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=admin_user,
        title="Revisão preventiva",
        description="Cliente solicitou revisão geral.",
        labor_cost=Decimal("100.00"),
        parts_cost=Decimal("50.00"),
        discount=Decimal("0.00"),
    )


@pytest.fixture
def receivable(service_order, customer, admin_user):
    return Receivable.objects.create(
        service_order=service_order,
        customer=customer,
        original_amount=Decimal("150.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("150.00"),
        paid_amount=Decimal("0.00"),
        created_by=admin_user,
    )


@pytest.fixture
def payment(receivable, admin_user):
    return Payment.objects.create(
        receivable=receivable,
        amount=Decimal("150.00"),
        method=PaymentMethod.PIX,
        paid_at=timezone.now(),
        created_by=admin_user,
    )


@pytest.fixture
def email_template():
    return MessageTemplate.objects.create(
        name="Template de teste por e-mail",
        code="teste_email",
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Olá {{ cliente_nome }}",
        body="Mensagem para {{ cliente_nome }} sobre a OS {{ os_numero }}.",
        available_variables=["cliente_nome", "os_numero"],
    )


@pytest.fixture
def inactive_email_template():
    return MessageTemplate.objects.create(
        name="Template inativo",
        code="template_inativo",
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        subject="Inativo",
        body="Corpo inativo",
        is_active=False,
    )


@pytest.fixture
def whatsapp_template():
    return MessageTemplate.objects.create(
        name="Template de teste WhatsApp",
        code="teste_whatsapp",
        channel=MessageChannel.WHATSAPP,
        message_type=MessageType.TRANSACTIONAL,
        subject="",
        body="Olá {{ cliente_nome }}, seu veículo está pronto.",
        available_variables=["cliente_nome"],
    )


@pytest.fixture
def queued_email(customer, attendant_user):
    return MessageQueue.objects.create(
        customer=customer,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Assunto da fila",
        body="Corpo da fila",
        created_by=attendant_user,
    )


@pytest.fixture
def sent_log(customer, attendant_user, queued_email):
    return MessageLog.objects.create(
        customer=customer,
        queue_message=queued_email,
        channel=MessageChannel.EMAIL,
        message_type=MessageType.TRANSACTIONAL,
        recipient=customer.email,
        subject="Assunto enviado",
        body_snapshot="Corpo enviado",
        status=MessageStatus.SENT,
        sent_at=timezone.now(),
        provider="django-email",
        provider_message_id="email-1",
        created_by=attendant_user,
    )


@pytest.fixture
def uploaded_attachment():
    return SimpleUploadedFile(
        "orcamento.pdf",
        b"conteudo fake do pdf",
        content_type="application/pdf",
    )
