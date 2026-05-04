from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from customers.models import Customer, Vehicle
from service_orders.forms import ServiceOrderApprovalForm
from service_orders.models import ServiceOrder
from service_orders.services import (
    approve_service_order_budget,
    change_service_order_status,
    get_allowed_next_statuses,
)


@pytest.fixture
def state_machine_data():
    User = get_user_model()

    user = User.objects.create_user(
        email="state-machine@example.com",
        password="StrongPassword123",
    )

    customer = Customer.objects.create(
        name="Cliente Máquina de Estados",
        phone="11999999999",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="SME1234",
        brand="Toyota",
        model="Corolla",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Teste de fluxo",
        description="Validar máquina de estados.",
        labor_cost=Decimal("100.00"),
    )

    return {
        "user": user,
        "customer": customer,
        "vehicle": vehicle,
        "service_order": service_order,
    }


@pytest.mark.django_db
def test_open_order_cannot_jump_directly_to_finished(state_machine_data):
    service_order = state_machine_data["service_order"]
    user = state_machine_data["user"]

    with pytest.raises(ValidationError):
        change_service_order_status(
            service_order=service_order,
            new_status=ServiceOrder.Status.FINISHED,
            changed_by=user,
        )


@pytest.mark.django_db
def test_formal_operational_flow_until_paid(state_machine_data):
    service_order = state_machine_data["service_order"]
    user = state_machine_data["user"]

    service_order = change_service_order_status(
        service_order=service_order,
        new_status=ServiceOrder.Status.IN_DIAGNOSIS,
        changed_by=user,
    )
    service_order = change_service_order_status(
        service_order=service_order,
        new_status=ServiceOrder.Status.WAITING_APPROVAL,
        changed_by=user,
    )

    approval_form = ServiceOrderApprovalForm(
        data={
            "channel": "in_person",
            "notes": "Cliente aprovou presencialmente.",
        }
    )
    assert approval_form.is_valid(), approval_form.errors
    approve_service_order_budget(
        service_order=service_order,
        form=approval_form,
        approved_by=user,
    )
    service_order.refresh_from_db()

    for status in [
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.FINISHED,
        ServiceOrder.Status.BILLED,
        ServiceOrder.Status.PAID,
    ]:
        service_order = change_service_order_status(
            service_order=service_order,
            new_status=status,
            changed_by=user,
        )

    service_order.refresh_from_db()
    assert service_order.status == ServiceOrder.Status.PAID
    assert service_order.finished_at is not None


@pytest.mark.django_db
def test_waiting_approval_can_be_approved_only_by_budget_approval(state_machine_data):
    service_order = state_machine_data["service_order"]
    user = state_machine_data["user"]

    service_order = change_service_order_status(
        service_order=service_order,
        new_status=ServiceOrder.Status.WAITING_APPROVAL,
        changed_by=user,
    )

    form = ServiceOrderApprovalForm(
        data={
            "channel": "in_person",
            "notes": "Cliente aprovou presencialmente.",
        }
    )

    assert form.is_valid(), form.errors

    approval = approve_service_order_budget(
        service_order=service_order,
        form=form,
        approved_by=user,
    )

    service_order.refresh_from_db()
    assert approval.service_order == service_order
    assert service_order.status == ServiceOrder.Status.APPROVED


@pytest.mark.django_db
def test_paid_order_has_no_next_statuses(state_machine_data):
    assert get_allowed_next_statuses(ServiceOrder.Status.PAID) == set()
