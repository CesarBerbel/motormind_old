from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from core.exceptions import PermissionDeniedError


def is_authenticated_user(user):
    return bool(user and user.is_authenticated and user.is_active)


def user_in_group(user, group_name):
    """
    Check whether an authenticated user belongs to a Django group.
    """
    if not is_authenticated_user(user):
        return False

    return user.groups.filter(name=group_name).exists()


def user_in_any_group(user, group_names):
    """
    Check whether a user belongs to at least one group from the given list.
    """
    if not is_authenticated_user(user):
        return False

    return user.groups.filter(name__in=group_names).exists()


def is_admin(user):
    """
    Global administrator check.
    """
    if not is_authenticated_user(user):
        return False

    return user.is_superuser or user_in_group(user, "Administrador")


def require_permission(permission_function, redirect_url="accounts:dashboard"):
    """
    Decorator for function-based views using MotorMind permission functions.

    Example:
        @login_required
        @require_permission(can_manage_financial)
        def my_view(request):
            ...
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(request, *args, **kwargs):
            if not permission_function(request.user):
                messages.error(
                    request, "Você não tem permissão para acessar esta área."
                )
                return redirect(redirect_url)

            return view_function(request, *args, **kwargs)

        return wrapper

    return decorator


def assert_permission(user, permission_function, message=None):
    """
    Raise a domain permission error when the user is not allowed.

    This is useful inside services, where redirect/messages should not be used.
    """
    if not permission_function(user):
        raise PermissionDeniedError(
            message or "Você não tem permissão para executar esta ação."
        )
