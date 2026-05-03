from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from core.exceptions import PermissionDeniedError

ADMIN_GROUP = "Administrador"
ATTENDANT_GROUP = "Atendente"
MECHANIC_GROUP = "Mecânico"
FINANCIAL_GROUP = "Financeiro"


def is_authenticated_user(user):
    """
    Check whether the given user is authenticated and active.
    """
    return bool(user and user.is_authenticated and user.is_active)


def user_in_group(user, group_name):
    """
    Check whether the authenticated user belongs to a specific group.

    Superusers are allowed automatically.
    """
    if not is_authenticated_user(user):
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()


def user_in_any_group(user, group_names):
    """
    Check whether the authenticated user belongs to at least one group.

    Superusers are allowed automatically.
    """
    if not is_authenticated_user(user):
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=group_names).exists()


def is_admin(user):
    """
    Check whether the user has administrator access.
    """
    return user_in_group(user, ADMIN_GROUP)


def is_attendant(user):
    """
    Check whether the user belongs to the attendant profile.
    """
    return user_in_group(user, ATTENDANT_GROUP)


def is_mechanic(user):
    """
    Check whether the user belongs to the mechanic profile.
    """
    return user_in_group(user, MECHANIC_GROUP)


def is_financial(user):
    """
    Check whether the user belongs to the financial profile.
    """
    return user_in_group(user, FINANCIAL_GROUP)


def can_access_customers(user):
    """
    Admin and attendant can access customer management.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_access_vehicles(user):
    """
    Admin, attendant and mechanic can access vehicles.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_view_service_orders(user):
    """
    Admin, attendant, mechanic and financial can view service orders.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
            FINANCIAL_GROUP,
        ],
    )


def can_manage_service_orders(user):
    """
    Admin and attendant can create and update commercial service order data.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_update_service_order_technical_data(user):
    """
    Admin and mechanic can update technical service order data.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_cancel_service_order(user):
    """
    Only admin can cancel service orders.
    """
    return is_admin(user)


def can_manage_service_order_items(user):
    """
    Admin and attendant can manage manual service order items.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_manage_service_order_notes(user):
    """
    Admin, attendant and mechanic can create service order notes.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_access_operational_board(user):
    """
    Admin, attendant and mechanic can access the operational board.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_access_workshop_agenda(user):
    """
    Admin, attendant and mechanic can access the workshop agenda.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_track_service_order_time(user):
    """
    Admin and mechanic can track service order time.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_finish_time_entry(user, time_entry):
    """
    Admin can finish any time entry.
    Mechanic can finish only their own time entry.
    """
    if is_admin(user):
        return True

    return is_mechanic(user) and time_entry.mechanic_id == user.id


def can_access_productivity_report(user):
    """
    Admin and attendant can access productivity reports.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_access_inventory(user):
    """
    Admin, attendant, mechanic and financial can view inventory.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
            FINANCIAL_GROUP,
        ],
    )


def can_manage_inventory(user):
    """
    Admin and attendant can create and update inventory parts.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_move_inventory_stock(user):
    """
    Admin and attendant can create stock movements.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_view_financial(user):
    """
    Admin and financial can view financial screens and dashboards.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            FINANCIAL_GROUP,
        ],
    )


def can_manage_financial(user):
    """
    Admin and financial can create financial records and register payments.
    """
    return user_in_any_group(
        user,
        [
            ADMIN_GROUP,
            FINANCIAL_GROUP,
        ],
    )


def assert_permission(user, permission_function, message=None):
    """
    Raise a domain permission error when the user is not allowed.

    Use this inside services, where redirects and messages should not exist.
    """
    if not permission_function(user):
        raise PermissionDeniedError(
            message or "Você não tem permissão para executar esta ação."
        )


def user_passes_permission(permission_check, message=None):
    """
    Decorator factory for function-based views.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if permission_check(request.user):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                message or "Você não tem permissão para acessar esta área.",
            )

            return redirect("accounts:dashboard")

        return wrapper

    return decorator


def groups_required(group_names):
    """
    Require at least one group for a function-based view.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_in_any_group(request.user, group_names):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "Você não tem permissão para acessar esta área.",
            )

            return redirect("accounts:dashboard")

        return wrapper

    return decorator


def role_required(group_name):
    """
    Require a single group for a function-based view.
    """
    return groups_required([group_name])
