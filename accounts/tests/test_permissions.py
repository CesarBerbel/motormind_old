import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from accounts.permissions import user_in_any_group, user_in_group


@pytest.mark.django_db
def test_user_in_group_returns_true_for_user_group():
    """
    Test if user_in_group returns true when user belongs to group.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="attendant@example.com",
        password="StrongPassword123",
    )

    group = Group.objects.create(name="Atendente")
    user.groups.add(group)

    assert user_in_group(user, "Atendente")


@pytest.mark.django_db
def test_user_in_group_returns_false_for_wrong_group():
    """
    Test if user_in_group returns false when user does not belong to group.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="mechanic@example.com",
        password="StrongPassword123",
    )

    Group.objects.create(name="Atendente")

    assert not user_in_group(user, "Atendente")


@pytest.mark.django_db
def test_user_in_any_group_returns_true_for_allowed_group():
    """
    Test if user_in_any_group returns true for one allowed group.
    """
    User = get_user_model()

    user = User.objects.create_user(
        email="admin@example.com",
        password="StrongPassword123",
    )

    group = Group.objects.create(name="Administrador")
    user.groups.add(group)

    assert user_in_any_group(
        user,
        [
            "Administrador",
            "Atendente",
        ],
    )


@pytest.mark.django_db
def test_superuser_has_access_to_any_group():
    """
    Test if superuser is accepted by user_in_any_group.
    """
    User = get_user_model()

    user = User.objects.create_superuser(
        email="root@example.com",
        password="StrongPassword123",
    )

    assert user_in_any_group(
        user,
        [
            "Financeiro",
        ],
    )
