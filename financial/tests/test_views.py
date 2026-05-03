import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from accounts.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    MECHANIC_GROUP,
)


@pytest.fixture
def users():
    User = get_user_model()
    groups = {
        name: Group.objects.get_or_create(name=name)[0]
        for name in [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
            FINANCIAL_GROUP,
        ]
    }
    result = {}

    for role, group_name in [
        ("admin", ADMIN_GROUP),
        ("attendant", ATTENDANT_GROUP),
        ("mechanic", MECHANIC_GROUP),
        ("financial", FINANCIAL_GROUP),
    ]:
        user = User.objects.create_user(
            email=f"{role}_dashboard@example.com",
            password="StrongPassword123",
        )
        user.groups.add(groups[group_name])
        result[role] = user

    return result


@pytest.mark.django_db
def test_financial_user_can_access_financial_dashboard(client, users):
    client.login(username=users["financial"].email, password="StrongPassword123")

    response = client.get(reverse("financial:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_can_access_financial_dashboard(client, users):
    client.login(username=users["admin"].email, password="StrongPassword123")

    response = client.get(reverse("financial:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_attendant_cannot_access_financial_dashboard(client, users):
    client.login(username=users["attendant"].email, password="StrongPassword123")

    response = client.get(reverse("financial:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url


@pytest.mark.django_db
def test_mechanic_cannot_access_financial_dashboard(client, users):
    client.login(username=users["mechanic"].email, password="StrongPassword123")

    response = client.get(reverse("financial:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:dashboard") in response.url
