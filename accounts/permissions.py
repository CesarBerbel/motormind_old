from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

ADMIN_GROUP = "Administrador"
ATTENDANT_GROUP = "Atendente"
MECHANIC_GROUP = "Mecânico"
FINANCIAL_GROUP = "Financeiro"


def is_authenticated_user(user):
    """
    Check if user is authenticated.
    """
    return bool(user and user.is_authenticated)


def has_group(user, group_name):
    """
    Check if user belongs to a specific group.

    Superusers are treated as allowed.
    """
    if not is_authenticated_user(user):
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()


def has_any_group(user, group_names):
    """
    Check if user belongs to at least one group.

    Superusers are treated as allowed.
    """
    if not is_authenticated_user(user):
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=group_names).exists()


def is_admin_user(user):
    """
    Check if user is an administrator.

    Admin means:
    - superuser
    - or member of Administrador group
    """
    return has_group(user, ADMIN_GROUP)


def is_attendant_user(user):
    """
    Check if user is an attendant.
    """
    return has_group(user, ATTENDANT_GROUP)


def is_mechanic_user(user):
    """
    Check if user is a mechanic.
    """
    return has_group(user, MECHANIC_GROUP)


def is_financial_user(user):
    """
    Check if user is a financial user.
    """
    return has_group(user, FINANCIAL_GROUP)


def can_access_customers(user):
    """
    Check if user can access customer management.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_access_vehicles(user):
    """
    Check if user can access vehicle management.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_view_service_orders(user):
    """
    Check if user can view service orders.
    """
    return has_any_group(
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
    Check if user can create and update administrative service order data.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_update_service_order_technical_data(user):
    """
    Check if user can update technical service order data.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_cancel_service_order(user):
    """
    Check if user can cancel service orders.
    """
    return is_admin_user(user)


def can_manage_service_order_items(user):
    """
    Check if user can manage service order items.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_manage_service_order_notes(user):
    """
    Check if user can create internal notes.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_access_operational_board(user):
    """
    Check if user can access operational board.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_access_workshop_agenda(user):
    """
    Check if user can access workshop agenda.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_track_service_order_time(user):
    """
    Check if user can start or finish time tracking.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            MECHANIC_GROUP,
        ],
    )


def can_finish_time_entry(user, time_entry):
    """
    Check if user can finish a time entry.

    Admins can finish any entry.
    Mechanics can finish only their own entries.
    """
    if is_admin_user(user):
        return True

    return is_mechanic_user(user) and time_entry.mechanic_id == user.id


def can_access_productivity_report(user):
    """
    Check if user can access mechanic productivity report.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def user_passes_permission(permission_check, message=None):
    """
    Decorator factory for permission checks.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if permission_check(request.user):
                return view_func(request, *args, **kwargs)

            if message:
                messages.error(request, message)
            else:
                messages.error(
                    request,
                    "Você não tem permissão para acessar esta área.",
                )

            return redirect("accounts:dashboard")

        return wrapper

    return decorator


def role_required(group_name):
    """
    Require a single group.

    Kept for backward compatibility with existing views.
    """
    return groups_required([group_name])


def groups_required(group_names):
    """
    Require at least one group.

    Superusers are allowed automatically.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if has_any_group(request.user, group_names):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "Você não tem permissão para acessar esta área.",
            )

            return redirect("accounts:dashboard")

        return wrapper

    return decorator


def can_access_inventory(user):
    """
    Check if user can access inventory screens.
    """
    return has_any_group(
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
    Check if user can create and update inventory parts.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )


def can_move_inventory_stock(user):
    """
    Check if user can create stock movements.
    """
    return has_any_group(
        user,
        [
            ADMIN_GROUP,
            ATTENDANT_GROUP,
        ],
    )
