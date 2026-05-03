import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group

from accounts.templatetags.group_tags import has_group


@pytest.mark.django_db
def test_has_group_returns_true_when_user_belongs_to_group():
    User = get_user_model()

    user = User.objects.create_user(
        email="group_filter_admin@example.com",
        password="StrongPassword123",
    )

    group = Group.objects.create(name="Administrador")
    user.groups.add(group)

    assert has_group(user, "Administrador") is True


@pytest.mark.django_db
def test_has_group_returns_false_when_user_does_not_belong_to_group():
    User = get_user_model()

    user = User.objects.create_user(
        email="group_filter_user@example.com",
        password="StrongPassword123",
    )

    Group.objects.create(name="Administrador")

    assert has_group(user, "Administrador") is False


@pytest.mark.django_db
def test_has_group_returns_false_for_anonymous_user():
    user = AnonymousUser()

    assert has_group(user, "Administrador") is False


@pytest.mark.django_db
def test_has_group_returns_true_for_superuser():
    User = get_user_model()

    user = User.objects.create_superuser(
        email="group_filter_superuser@example.com",
        password="StrongPassword123",
    )

    assert has_group(user, "Administrador") is True
