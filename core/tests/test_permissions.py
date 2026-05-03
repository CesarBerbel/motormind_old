import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group

from core.exceptions import PermissionDeniedError
from core.permissions import (
    assert_permission,
    is_admin,
    is_authenticated_user,
    user_in_any_group,
    user_in_group,
)


@pytest.mark.django_db
def test_is_authenticated_user_returns_false_for_anonymous_user():
    assert is_authenticated_user(AnonymousUser()) is False


@pytest.mark.django_db
def test_is_authenticated_user_returns_true_for_active_authenticated_user():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_permission_user@example.com",
        password="StrongPassword123",
    )

    assert is_authenticated_user(user) is True


@pytest.mark.django_db
def test_user_in_group_returns_true_when_user_belongs_to_group():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_group_user@example.com",
        password="StrongPassword123",
    )
    group = Group.objects.create(name="Administrador")
    user.groups.add(group)

    assert user_in_group(user, "Administrador") is True


@pytest.mark.django_db
def test_user_in_group_returns_false_when_user_does_not_belong_to_group():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_no_group_user@example.com",
        password="StrongPassword123",
    )

    assert user_in_group(user, "Administrador") is False


@pytest.mark.django_db
def test_user_in_any_group_returns_true_for_one_matching_group():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_any_group_user@example.com",
        password="StrongPassword123",
    )
    group = Group.objects.create(name="Financeiro")
    user.groups.add(group)

    assert user_in_any_group(user, ["Administrador", "Financeiro"]) is True


@pytest.mark.django_db
def test_is_admin_returns_true_for_superuser():
    User = get_user_model()
    user = User.objects.create_superuser(
        email="core_superuser@example.com",
        password="StrongPassword123",
    )

    assert is_admin(user) is True


@pytest.mark.django_db
def test_is_admin_returns_true_for_administrador_group():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_admin_group@example.com",
        password="StrongPassword123",
    )
    group = Group.objects.create(name="Administrador")
    user.groups.add(group)

    assert is_admin(user) is True


@pytest.mark.django_db
def test_is_admin_returns_false_for_regular_user():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_regular_user@example.com",
        password="StrongPassword123",
    )

    assert is_admin(user) is False


@pytest.mark.django_db
def test_assert_permission_does_not_raise_when_permission_is_allowed():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_allowed_user@example.com",
        password="StrongPassword123",
    )

    assert_permission(user, lambda current_user: True)


@pytest.mark.django_db
def test_assert_permission_raises_when_permission_is_denied():
    User = get_user_model()
    user = User.objects.create_user(
        email="core_denied_user@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(PermissionDeniedError):
        assert_permission(user, lambda current_user: False)
