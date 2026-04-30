from datetime import date
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle
from service_orders.forms import ServiceOrderForm, ServiceOrderItemForm
from service_orders.models import ServiceOrder, ServiceOrderItem


@pytest.fixture
def attendant_user():
    """
    Create an attendant user.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="localization_attendant@example.com",
        password="StrongPassword123",
    )

    group, _created = Group.objects.get_or_create(name="Atendente")
    user.groups.add(group)

    return user


@pytest.fixture
def service_order_data(attendant_user):
    """
    Create data required for localization tests.
    """
    customer = Customer.objects.create(
        name="Cliente Localização",
        phone="+55 11 99999-9999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="ABC-1234",
        brand="Fiat",
        model="Uno",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=attendant_user,
        title="Revisão de localização",
        description="Teste de localização pt-BR.",
        labor_cost=Decimal("150.00"),
        parts_cost=Decimal("200.00"),
        discount=Decimal("50.00"),
        expected_delivery_date=date(2026, 5, 15),
    )

    ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.SERVICE,
        description="Troca de óleo",
        quantity=Decimal("1.00"),
        unit_price=Decimal("120.00"),
    )

    ServiceOrderItem.objects.create(
        service_order=service_order,
        item_type=ServiceOrderItem.ItemType.PART,
        description="Filtro de óleo",
        quantity=Decimal("2.00"),
        unit_price=Decimal("35.50"),
    )

    return {
        "customer": customer,
        "vehicle": vehicle,
        "service_order": service_order,
        "user": attendant_user,
    }


def test_project_uses_brazilian_language_and_timezone():
    """
    Test if project localization settings are configured for Brazil.
    """
    assert settings.LANGUAGE_CODE == "pt-br"
    assert settings.TIME_ZONE == "America/Sao_Paulo"
    assert settings.DATE_FORMAT == "d/m/Y"
    assert settings.DATETIME_FORMAT == "d/m/Y H:i"
    assert settings.DECIMAL_SEPARATOR == ","
    assert settings.THOUSAND_SEPARATOR == "."
    assert settings.USE_THOUSAND_SEPARATOR is True


@pytest.mark.django_db
def test_service_order_form_has_brazilian_money_placeholders():
    """
    Test if service order financial fields use Brazilian placeholders.
    """
    form = ServiceOrderForm()

    assert form.fields["labor_cost"].widget.attrs["placeholder"] == "Ex: 150,00"
    assert form.fields["parts_cost"].widget.attrs["placeholder"] == "Ex: 200,00"
    assert form.fields["discount"].widget.attrs["placeholder"] == "Ex: 50,00"


@pytest.mark.django_db
def test_service_order_item_form_has_brazilian_money_placeholder():
    """
    Test if item unit price field uses Brazilian placeholder.
    """
    form = ServiceOrderItemForm()

    assert form.fields["unit_price"].widget.attrs["placeholder"] == "Ex: 100,00"


@pytest.mark.django_db
def test_service_order_edit_form_displays_expected_delivery_date(
    service_order_data,
):
    """
    Test if expected delivery date appears correctly in edit form.
    """
    service_order = service_order_data["service_order"]

    form = ServiceOrderForm(instance=service_order)

    rendered_field = str(form["expected_delivery_date"])

    assert 'value="2026-05-15"' in rendered_field


@pytest.mark.django_db
def test_service_order_detail_displays_brl_currency(
    client,
    service_order_data,
):
    """
    Test if service order detail page displays values in Brazilian Real.
    """
    user = service_order_data["user"]
    service_order = service_order_data["service_order"]

    client.login(
        username=user.email,
        password="StrongPassword123",
    )

    response = client.get(
        reverse(
            "service_orders:service_order_detail",
            args=[service_order.pk],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "R$ 191,00" in content
    assert "R$ 150,00" in content
    assert "R$ 200,00" in content
    assert "R$ 50,00" in content
    assert "R$ 491,00" in content
    assert "15/05/2026" in content
