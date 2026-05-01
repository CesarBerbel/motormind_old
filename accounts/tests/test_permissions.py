import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group

from accounts.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    MECHANIC_GROUP,
    can_access_customers,
    can_access_operational_board,
    can_access_productivity_report,
    can_cancel_service_order,
    can_finish_time_entry,
    can_manage_service_orders,
    can_track_service_order_time,
    can_view_service_orders,
    has_any_group,
    has_group,
    is_admin_user,
)


@pytest.fixture
def users():
    """
    Create users for permission tests.
    """
    User = get_user_model()

    admin = User.objects.create_user(
        email="permissions_admin@example.com",
        password="StrongPassword123",
    )

    attendant = User.objects.create_user(
        email="permissions_attendant@example.com",
        password="StrongPassword123",
    )

    mechanic = User.objects.create_user(
        email="permissions_mechanic@example.com",
        password="StrongPassword123",
    )

    financial = User.objects.create_user(
        email="permissions_financial@example.com",
        password="StrongPassword123",
    )

    plain_user = User.objects.create_user(
        email="permissions_plain@example.com",
        password="StrongPassword123",
    )

    superuser = User.objects.create_superuser(
        email="permissions_superuser@example.com",
        password="StrongPassword123",
    )

    admin_group, _created = Group.objects.get_or_create(name=ADMIN_GROUP)
    attendant_group, _created = Group.objects.get_or_create(name=ATTENDANT_GROUP)
    mechanic_group, _created = Group.objects.get_or_create(name=MECHANIC_GROUP)
    financial_group, _created = Group.objects.get_or_create(name=FINANCIAL_GROUP)

    admin.groups.add(admin_group)
    attendant.groups.add(attendant_group)
    mechanic.groups.add(mechanic_group)
    financial.groups.add(financial_group)

    return {
        "admin": admin,
        "attendant": attendant,
        "mechanic": mechanic,
        "financial": financial,
        "plain_user": plain_user,
        "superuser": superuser,
    }


class FakeTimeEntry:
    """
    Simple object used to test permission logic.
    """

    def __init__(self, mechanic_id):
        self.mechanic_id = mechanic_id


@pytest.mark.django_db
def test_has_group_allows_group_member(users):
    """
    Test if has_group returns true for group member.
    """
    assert has_group(users["admin"], ADMIN_GROUP) is True


@pytest.mark.django_db
def test_has_group_denies_plain_user(users):
    """
    Test if has_group returns false for user without group.
    """
    assert has_group(users["plain_user"], ADMIN_GROUP) is False


@pytest.mark.django_db
def test_has_group_allows_superuser(users):
    """
    Test if superuser is allowed by group helper.
    """
    assert has_group(users["superuser"], ADMIN_GROUP) is True


@pytest.mark.django_db
def test_has_any_group_allows_one_matching_group(users):
    """
    Test if has_any_group accepts at least one matching group.
    """
    assert (
        has_any_group(
            users["mechanic"],
            [
                ADMIN_GROUP,
                MECHANIC_GROUP,
            ],
        )
        is True
    )


@pytest.mark.django_db
def test_has_any_group_denies_anonymous_user():
    """
    Test if anonymous user is denied.
    """
    assert (
        has_any_group(
            AnonymousUser(),
            [
                ADMIN_GROUP,
            ],
        )
        is False
    )


@pytest.mark.django_db
def test_is_admin_user_with_superuser(users):
    """
    Test if superuser is treated as admin.
    """
    assert is_admin_user(users["superuser"]) is True


@pytest.mark.django_db
def test_can_access_customers(users):
    """
    Test customer access permissions.
    """
    assert can_access_customers(users["admin"]) is True
    assert can_access_customers(users["attendant"]) is True
    assert can_access_customers(users["mechanic"]) is False


@pytest.mark.django_db
def test_can_view_service_orders(users):
    """
    Test service order view permissions.
    """
    assert can_view_service_orders(users["admin"]) is True
    assert can_view_service_orders(users["attendant"]) is True
    assert can_view_service_orders(users["mechanic"]) is True
    assert can_view_service_orders(users["financial"]) is True
    assert can_view_service_orders(users["plain_user"]) is False


@pytest.mark.django_db
def test_can_manage_service_orders(users):
    """
    Test service order management permissions.
    """
    assert can_manage_service_orders(users["admin"]) is True
    assert can_manage_service_orders(users["attendant"]) is True
    assert can_manage_service_orders(users["mechanic"]) is False
    assert can_manage_service_orders(users["financial"]) is False


@pytest.mark.django_db
def test_can_cancel_service_order(users):
    """
    Test service order cancellation permission.
    """
    assert can_cancel_service_order(users["admin"]) is True
    assert can_cancel_service_order(users["superuser"]) is True
    assert can_cancel_service_order(users["attendant"]) is False


@pytest.mark.django_db
def test_can_access_operational_board(users):
    """
    Test board access permissions.
    """
    assert can_access_operational_board(users["admin"]) is True
    assert can_access_operational_board(users["attendant"]) is True
    assert can_access_operational_board(users["mechanic"]) is True
    assert can_access_operational_board(users["financial"]) is False


@pytest.mark.django_db
def test_can_track_service_order_time(users):
    """
    Test time tracking permissions.
    """
    assert can_track_service_order_time(users["admin"]) is True
    assert can_track_service_order_time(users["mechanic"]) is True
    assert can_track_service_order_time(users["attendant"]) is False


@pytest.mark.django_db
def test_can_finish_time_entry(users):
    """
    Test if mechanic can finish only own entry and admin can finish any entry.
    """
    mechanic_entry = FakeTimeEntry(mechanic_id=users["mechanic"].id)

    assert can_finish_time_entry(users["mechanic"], mechanic_entry) is True
    assert can_finish_time_entry(users["admin"], mechanic_entry) is True
    assert can_finish_time_entry(users["superuser"], mechanic_entry) is True
    assert can_finish_time_entry(users["attendant"], mechanic_entry) is False


@pytest.mark.django_db
def test_can_access_productivity_report(users):
    """
    Test productivity report permissions.
    """
    assert can_access_productivity_report(users["admin"]) is True
    assert can_access_productivity_report(users["attendant"]) is True
    assert can_access_productivity_report(users["mechanic"]) is False
    assert can_access_productivity_report(users["financial"]) is False
