from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from inventory.models import Part
from inventory.selectors import (
    get_critical_parts_with_priority,
    get_restock_priority,
    get_restock_suggestion_quantity,
)


@pytest.fixture
def user():
    """
    Create user with inventory access.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="critical_parts@example.com",
        password="StrongPassword123",
    )

    group, _created = Group.objects.get_or_create(name="Atendente")
    user.groups.add(group)

    return user


@pytest.fixture
def parts():
    """
    Create parts with different stock priority levels.
    """
    critical_zero = Part.objects.create(
        name="Peça zerada",
        internal_code="CRIT-ZERO-001",
        current_stock=Decimal("0.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    critical_low = Part.objects.create(
        name="Peça muito baixa",
        internal_code="CRIT-LOW-001",
        current_stock=Decimal("1.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    high = Part.objects.create(
        name="Peça alta reposição",
        internal_code="HIGH-001",
        current_stock=Decimal("3.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    medium = Part.objects.create(
        name="Peça média reposição",
        internal_code="MED-001",
        current_stock=Decimal("4.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    normal = Part.objects.create(
        name="Peça normal",
        internal_code="NORM-001",
        current_stock=Decimal("10.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
    )

    inactive_low = Part.objects.create(
        name="Peça inativa baixa",
        internal_code="INACTIVE-LOW-001",
        current_stock=Decimal("0.00"),
        minimum_stock=Decimal("4.00"),
        cost_price=Decimal("10.00"),
        sale_price=Decimal("20.00"),
        is_active=False,
    )

    return {
        "critical_zero": critical_zero,
        "critical_low": critical_low,
        "high": high,
        "medium": medium,
        "normal": normal,
        "inactive_low": inactive_low,
    }


@pytest.mark.django_db
def test_restock_priority_levels(parts):
    """
    Test restock priority calculation.
    """
    assert get_restock_priority(parts["critical_zero"])["level"] == "critical"
    assert get_restock_priority(parts["critical_low"])["level"] == "critical"
    assert get_restock_priority(parts["high"])["level"] == "high"
    assert get_restock_priority(parts["medium"])["level"] == "medium"
    assert get_restock_priority(parts["normal"])["level"] == "normal"


@pytest.mark.django_db
def test_restock_suggestion_quantity(parts):
    """
    Test restock suggestion quantity.
    """
    assert get_restock_suggestion_quantity(parts["critical_zero"]) == Decimal("8.00")
    assert get_restock_suggestion_quantity(parts["critical_low"]) == Decimal("7.00")
    assert get_restock_suggestion_quantity(parts["high"]) == Decimal("5.00")
    assert get_restock_suggestion_quantity(parts["medium"]) == Decimal("4.00")
    assert get_restock_suggestion_quantity(parts["normal"]) == 0


@pytest.mark.django_db
def test_critical_parts_selector_excludes_normal_and_inactive_parts(parts):
    """
    Test if selector returns only active low stock parts.
    """
    rows = get_critical_parts_with_priority()
    part_names = [row["part"].name for row in rows]

    assert parts["critical_zero"].name in part_names
    assert parts["critical_low"].name in part_names
    assert parts["high"].name in part_names
    assert parts["medium"].name in part_names
    assert parts["normal"].name not in part_names
    assert parts["inactive_low"].name not in part_names


@pytest.mark.django_db
def test_critical_parts_view_requires_login(client):
    """
    Test if critical parts view requires login.
    """
    response = client.get(reverse("inventory:critical_parts"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_user_can_access_critical_parts_view(client, user, parts):
    """
    Test if authorized user can access critical parts screen.
    """
    client.login(
        username=user.email,
        password="StrongPassword123",
    )

    response = client.get(reverse("inventory:critical_parts"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Peças críticas" in content
    assert parts["critical_zero"].name in content
    assert parts["critical_low"].name in content
    assert parts["high"].name in content
    assert parts["medium"].name in content
    assert parts["normal"].name not in content
    assert parts["inactive_low"].name not in content
    assert "Sugestão de compra" in content
