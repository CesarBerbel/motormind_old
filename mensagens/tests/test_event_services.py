import pytest
from django.test import override_settings

from mensagens.management.commands.seed_message_templates import TEMPLATES
from mensagens.models import MessageChannel, MessageQueue, MessageTemplate, MessageType
from mensagens.services import (
    build_service_order_message_variables,
    enqueue_customer_portal_first_access_message,
    enqueue_payment_received_message,
    enqueue_service_order_opened_message,
    enqueue_vehicle_ready_message,
    get_portal_url,
    get_vehicle_identification,
    get_workshop_name,
)


@pytest.fixture
def seeded_message_templates():
    for data in TEMPLATES:
        MessageTemplate.objects.update_or_create(
            code=data["code"],
            defaults={**data, "available_variables": ["cliente_nome"]},
        )


@pytest.mark.django_db
def test_get_workshop_name_uses_default_when_setting_is_missing(settings):
    if hasattr(settings, "MOTORMIND_WORKSHOP_NAME"):
        delattr(settings, "MOTORMIND_WORKSHOP_NAME")

    assert get_workshop_name() == "MotorMind"


@pytest.mark.django_db
@override_settings(MOTORMIND_WORKSHOP_NAME="Oficina Modelo")
def test_get_workshop_name_uses_setting():
    assert get_workshop_name() == "Oficina Modelo"


@pytest.mark.django_db
def test_get_portal_url_uses_default_when_setting_is_missing(settings):
    if hasattr(settings, "MOTORMIND_PORTAL_URL"):
        delattr(settings, "MOTORMIND_PORTAL_URL")

    assert get_portal_url() == "http://127.0.0.1:8000/portal/"


@pytest.mark.django_db
@override_settings(MOTORMIND_PORTAL_URL="https://oficina.exemplo.com/portal/")
def test_get_portal_url_uses_setting():
    assert get_portal_url() == "https://oficina.exemplo.com/portal/"


@pytest.mark.django_db
def test_get_vehicle_identification_uses_plate_brand_and_model(vehicle):
    assert get_vehicle_identification(vehicle) == "MSG-0001 - Volkswagen Gol"


@pytest.mark.django_db
def test_get_vehicle_identification_handles_missing_brand_and_model(vehicle):
    vehicle.brand = ""
    vehicle.model = ""

    assert get_vehicle_identification(vehicle) == "MSG-0001"


@pytest.mark.django_db
def test_get_vehicle_identification_handles_missing_plate(vehicle):
    vehicle.plate = ""

    assert get_vehicle_identification(vehicle) == "sem placa - Volkswagen Gol"


@pytest.mark.django_db
def test_build_service_order_message_variables_contains_standard_payload(service_order):
    variables = build_service_order_message_variables(service_order)

    assert variables["cliente_nome"] == service_order.customer.name
    assert variables["cpf_cnpj"] == service_order.customer.document
    assert variables["os_numero"] == service_order.number
    assert variables["veiculo_identificacao"] == "MSG-0001 - Volkswagen Gol"
    assert variables["portal_url"]
    assert variables["nome_oficina"]


@pytest.mark.django_db
def test_build_service_order_message_variables_allows_extra_variables(service_order):
    variables = build_service_order_message_variables(
        service_order,
        {"valor_total": "R$ 150,00", "custom": "valor"},
    )

    assert variables["valor_total"] == "R$ 150,00"
    assert variables["custom"] == "valor"


@pytest.mark.django_db
def test_enqueue_service_order_opened_message_uses_official_template(
    service_order, seeded_message_templates
):
    queue_message = enqueue_service_order_opened_message(service_order)

    assert queue_message.template.code == "abertura_os_email"
    assert queue_message.channel == MessageChannel.EMAIL
    assert queue_message.message_type == MessageType.TRANSACTIONAL
    assert str(service_order.number) in queue_message.subject
    assert queue_message.related_object == service_order


@pytest.mark.django_db
def test_enqueue_vehicle_ready_message_uses_whatsapp_template(
    service_order, seeded_message_templates
):
    queue_message = enqueue_vehicle_ready_message(service_order)

    assert queue_message.template.code == "veiculo_pronto_whatsapp"
    assert queue_message.channel == MessageChannel.WHATSAPP
    assert "pronto" in queue_message.body.lower()
    assert queue_message.related_object == service_order


@pytest.mark.django_db
def test_enqueue_payment_received_message_uses_payment_context(
    payment, seeded_message_templates
):
    queue_message = enqueue_payment_received_message(payment)

    assert queue_message.template.code == "pagamento_recebido_email"
    assert queue_message.channel == MessageChannel.EMAIL
    assert "150.00" in queue_message.body
    assert queue_message.related_object == payment


@pytest.mark.django_db
def test_enqueue_customer_portal_first_access_message_includes_initial_password(
    customer, service_order, seeded_message_templates
):
    queue_message = enqueue_customer_portal_first_access_message(
        customer=customer,
        service_order=service_order,
        initial_password="SenhaInicial123!",
    )

    assert queue_message.template.code == "primeiro_acesso_portal_email"
    assert "SenhaInicial123!" in queue_message.body
    assert queue_message.related_object == service_order
    assert MessageQueue.objects.count() == 1
