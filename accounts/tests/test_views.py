import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_login_page_loads(client):
    """
    Test if login page loads successfully.
    """
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert "Entrar no sistema" in response.content.decode()


@pytest.mark.django_db
def test_register_page_loads(client):
    """
    Test if register page loads successfully.
    """
    response = client.get(reverse("accounts:register"))

    assert response.status_code == 200
    assert "Criar conta" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    """
    Test if dashboard redirects anonymous users.
    """
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_authenticated_user_can_access_dashboard(client):
    """
    Test if authenticated user can access dashboard.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="user@example.com",
        password="StrongPassword123",
    )

    client.login(
        username="user@example.com",
        password="StrongPassword123",
    )

    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert user.email in response.content.decode()
