from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from inventory.models import Part


@pytest.fixture
def user():
    """
    Create user for dashboard inventory tests.
    """
    User = get_user_model()

    return User.objects.create_user(
        email="dashboard_inventory@example.com",
        password="StrongPassword123",
    )


@pytest.mark.django_db
def test_dashboard_shows_low_stock_parts_counter(client, user):
    """
    Test if dashboard shows low stock parts counter.
    """
    Part.objects.create(
        name="Pastilha baixa",
        internal_code="LOW-DASH-001",
        current_stock=Decimal("1.00"),
        minimum_stock=Decimal("2.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    Part.objects.create(
        name="Filtro normal",
        internal_code="OK-DASH-001",
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("2.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    client.login(
        username=user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Peças com estoque baixo" in content
    assert "Ver peças críticas" in content
    assert reverse("inventory:critical_parts") in content
    assert ">1<" in content.replace("\n", "").replace(" ", "")
