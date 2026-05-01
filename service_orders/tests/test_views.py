import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder, ServiceOrderHistory


@pytest.fixture
def create_user_with_group():
    """
    Create a user with a specific group.
    """

    def _create_user_with_group(email, group_name):
        User = get_user_model()

        user = User.objects.create_user(
            email=email,
            password="StrongPassword123",
        )

        group, _created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        return user

    return _create_user_with_group


@pytest.fixture
def order_data(create_user_with_group):
    """
    Create data required to test service order views.
    """
    user = create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    customer = Customer.objects.create(
        name="Cliente Teste",
        phone="+351 910 000 000",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )

    service_order = ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Troca de óleo",
        description="Trocar óleo e filtro.",
    )

    return {
        "user": user,
        "customer": customer,
        "vehicle": vehicle,
        "service_order": service_order,
    }


@pytest.mark.django_db
def test_service_order_list_requires_login(client):
    """
    Test if service order list requires login.
    """
    response = client.get(reverse("service_orders:service_order_list"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_attendant_can_access_service_order_list(
    client,
    create_user_with_group,
):
    """
    Test if attendant can access service order list.
    """
    create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_financial_can_access_service_order_list(
    client,
    create_user_with_group,
):
    """
    Test if financial user can access service order list.
    """
    create_user_with_group(
        "financial@example.com",
        "Financeiro",
    )

    client.login(
        username="financial@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_financial_cannot_create_service_order(
    client,
    create_user_with_group,
):
    """
    Test if financial user cannot create service order.
    """
    create_user_with_group(
        "financial@example.com",
        "Financeiro",
    )

    client.login(
        username="financial@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:service_order_create"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_attendant_can_create_service_order(
    client,
    order_data,
):
    """
    Test if attendant can create a service order.
    """
    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse("service_orders:service_order_create"),
        data={
            "customer": order_data["customer"].pk,
            "vehicle": order_data["vehicle"].pk,
            "title": "Alinhamento",
            "description": "Fazer alinhamento e balanceamento.",
            "priority": ServiceOrder.Priority.MEDIUM,
            "diagnosis": "",
            "solution": "",
            "status": ServiceOrder.Status.OPEN,
            "labor_cost": "50.00",
            "parts_cost": "0.00",
            "discount": "0.00",
            "expected_delivery_date": "",
        },
    )

    assert response.status_code == 302
    assert ServiceOrder.objects.filter(title="Alinhamento").exists()


@pytest.mark.django_db
def test_mechanic_can_update_technical_data(
    client,
    order_data,
    create_user_with_group,
):
    """
    Test if mechanic can update technical data.
    """
    create_user_with_group(
        "mechanic@example.com",
        "Mecânico",
    )

    client.login(
        username="mechanic@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_technical_update",
            args=[order_data["service_order"].pk],
        ),
        data={
            "diagnosis": "Filtro obstruído.",
            "solution": "Filtro substituído.",
            "status": ServiceOrder.Status.FINISHED,
        },
    )

    order_data["service_order"].refresh_from_db()

    assert response.status_code == 302
    assert order_data["service_order"].diagnosis == "Filtro obstruído."
    assert order_data["service_order"].status == ServiceOrder.Status.FINISHED
    assert order_data["service_order"].finished_at is not None


@pytest.mark.django_db
def test_admin_can_cancel_service_order(
    client,
    order_data,
    create_user_with_group,
):
    """
    Test if administrator can cancel service order.
    """
    create_user_with_group(
        "admin_cancel@example.com",
        "Administrador",
    )

    client.login(
        username="admin_cancel@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_cancel",
            args=[order_data["service_order"].pk],
        )
    )

    order_data["service_order"].refresh_from_db()

    assert response.status_code == 302
    assert order_data["service_order"].status == ServiceOrder.Status.CANCELED


@pytest.mark.django_db
def test_vehicles_by_customer_returns_only_customer_vehicles(
    client,
    create_user_with_group,
):
    """
    Test if AJAX endpoint returns only vehicles from selected customer.
    """
    create_user_with_group(
        "attendant@example.com",
        "Atendente",
    )

    client.login(
        username="attendant@example.com",
        password="StrongPassword123",
    )

    customer = Customer.objects.create(
        name="Cliente Um",
        phone="+351 910 000 000",
    )

    other_customer = Customer.objects.create(
        name="Cliente Dois",
        phone="+351 920 000 000",
    )

    vehicle = Vehicle.objects.create(
        customer=customer,
        plate="AA-00-AA",
        brand="Toyota",
        model="Corolla",
    )

    Vehicle.objects.create(
        customer=other_customer,
        plate="BB-11-BB",
        brand="Ford",
        model="Focus",
    )

    response = client.get(
        reverse("service_orders:vehicles_by_customer"),
        {
            "customer_id": customer.pk,
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert len(data["vehicles"]) == 1
    assert data["vehicles"][0]["id"] == vehicle.id
    assert data["vehicles"][0]["text"] == "AA-00-AA - Toyota Corolla"


@pytest.mark.django_db
def test_vehicles_by_customer_denies_financial_user(
    client,
    create_user_with_group,
):
    """
    Test if financial user cannot access AJAX endpoint.
    """
    create_user_with_group(
        "financial@example.com",
        "Financeiro",
    )

    client.login(
        username="financial@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("service_orders:vehicles_by_customer"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_mechanic_update_creates_service_order_history(
    client,
    order_data,
    create_user_with_group,
):
    """
    Test if technical update creates service order history.
    """
    create_user_with_group(
        "mechanic_history@example.com",
        "Mecânico",
    )

    client.login(
        username="mechanic_history@example.com",
        password="StrongPassword123",
    )

    response = client.post(
        reverse(
            "service_orders:service_order_technical_update",
            args=[order_data["service_order"].pk],
        ),
        data={
            "diagnosis": "Novo diagnóstico técnico.",
            "solution": "Nova solução aplicada.",
            "status": ServiceOrder.Status.IN_PROGRESS,
        },
    )

    assert response.status_code == 302

    assert ServiceOrderHistory.objects.filter(
        service_order=order_data["service_order"],
        field_name="diagnosis",
        new_value="Novo diagnóstico técnico.",
    ).exists()

    assert ServiceOrderHistory.objects.filter(
        service_order=order_data["service_order"],
        field_name="solution",
        new_value="Nova solução aplicada.",
    ).exists()

    assert ServiceOrderHistory.objects.filter(
        service_order=order_data["service_order"],
        field_name="status",
        old_value=ServiceOrder.Status.OPEN,
        new_value=ServiceOrder.Status.IN_PROGRESS,
    ).exists()
