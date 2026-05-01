import pytest
from django.contrib.auth import get_user_model
from accounts.utils import is_admin_user

@pytest.mark.django_db
def test_create_user_with_email():
    """
    Test if a regular user can be created with email as username.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="user@example.com",
        password="StrongPassword123",
    )

    assert user.email == "user@example.com"
    assert user.username is None
    assert user.check_password("StrongPassword123")
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_create_superuser_with_email():
    """
    Test if a superuser can be created with email.
    """
    User = get_user_model()

    user = User.objects.create_superuser(
        email="admin@example.com",
        password="StrongPassword123",
    )

    assert user.email == "admin@example.com"
    assert user.is_staff
    assert user.is_superuser
    assert user.is_active


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """
    Test if creating a user without email raises an error.
    """
    User = get_user_model()

    with pytest.raises(ValueError):
        User.objects.create_user(
            email="",
            password="StrongPassword123",
        )


@pytest.mark.django_db
def test_is_admin_user_with_superuser():

    User = get_user_model()

    superuser = User.objects.create_superuser(
        email="admin@example.com",
        password="StrongPassword123",
    )

    assert is_admin_user(superuser) is True
