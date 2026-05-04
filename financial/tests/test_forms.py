from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from customers.models import Customer, Vehicle
from financial.forms import ExpenseForm, PaymentForm, ReceivableCreateForm
from financial.models import Receivable
from service_orders.models import ServiceOrder


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="financial_forms@example.com",
        password="StrongPassword123",
    )


@pytest.fixture
def service_order(user):
    customer = Customer.objects.create(name="Cliente Form", phone="11999999999")
    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="FRM-0001",
        brand="Fiat",
        model="Uno",
    )
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="OS finalizada",
        description="OS disponível para cobrança.",
        status=ServiceOrder.Status.FINISHED,
        finished_at=timezone.now(),
    )


@pytest.mark.django_db
def test_receivable_create_form_lists_only_finished_orders_without_receivable(
    service_order,
    user,
):
    form = ReceivableCreateForm()

    assert service_order in form.fields["service_order"].queryset

    Receivable.objects.create(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("10.00"),
        created_by=user,
    )

    form = ReceivableCreateForm()

    assert service_order not in form.fields["service_order"].queryset


@pytest.mark.django_db
def test_payment_form_rejects_amount_above_remaining(service_order, user):
    receivable = Receivable.objects.create(
        service_order=service_order,
        customer=service_order.customer,
        original_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        final_amount=Decimal("100.00"),
        created_by=user,
    )

    form = PaymentForm(
        data={
            "amount": "100.01",
            "method": "pix",
            "notes": "",
        },
        receivable=receivable,
    )

    assert form.is_valid() is False
    assert "amount" in form.errors


@pytest.mark.django_db
def test_financial_forms_apply_bootstrap_visual_classes(service_order):
    receivable_form = ReceivableCreateForm()
    expense_form = ExpenseForm()

    assert (
        "form-select" in receivable_form.fields["service_order"].widget.attrs["class"]
    )
    assert "form-control" in receivable_form.fields["due_date"].widget.attrs["class"]
    assert "form-control" in expense_form.fields["description"].widget.attrs["class"]
    assert "form-control" in expense_form.fields["amount"].widget.attrs["class"]
    assert "form-control" in expense_form.fields["notes"].widget.attrs["class"]
