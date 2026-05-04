import pytest

from core.permissions import can_manage_messages, can_send_messages, can_view_messages


@pytest.mark.django_db
def test_admin_can_view_manage_and_send_messages(admin_user):
    assert can_view_messages(admin_user) is True
    assert can_manage_messages(admin_user) is True
    assert can_send_messages(admin_user) is True


@pytest.mark.django_db
def test_attendant_can_view_and_send_but_cannot_manage_messages(attendant_user):
    assert can_view_messages(attendant_user) is True
    assert can_manage_messages(attendant_user) is False
    assert can_send_messages(attendant_user) is True


@pytest.mark.django_db
def test_financial_can_view_and_send_but_cannot_manage_messages(financial_user):
    assert can_view_messages(financial_user) is True
    assert can_manage_messages(financial_user) is False
    assert can_send_messages(financial_user) is True


@pytest.mark.django_db
def test_mechanic_cannot_access_message_module(mechanic_user):
    assert can_view_messages(mechanic_user) is False
    assert can_manage_messages(mechanic_user) is False
    assert can_send_messages(mechanic_user) is False


@pytest.mark.django_db
def test_plain_user_cannot_access_message_module(plain_user):
    assert can_view_messages(plain_user) is False
    assert can_manage_messages(plain_user) is False
    assert can_send_messages(plain_user) is False


@pytest.mark.django_db
def test_superuser_is_allowed_by_group_helpers(superuser):
    assert can_view_messages(superuser) is True
    assert can_manage_messages(superuser) is True
    assert can_send_messages(superuser) is True
