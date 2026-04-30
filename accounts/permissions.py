from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect


def user_in_group(user, group_name):
    """
    Check if the authenticated user belongs to a specific group.
    """
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def user_in_any_group(user, group_names):
    """
    Check if the authenticated user belongs to any group from the list.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=group_names).exists()


def is_admin(user):
    """
    Check if user is an administrator.
    """
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrador").exists()
    )


def is_attendant(user):
    """
    Check if user is an attendant.
    """
    return user_in_group(user, "Atendente")


def is_mechanic(user):
    """
    Check if user is a mechanic.
    """
    return user_in_group(user, "Mecânico")


def is_financial(user):
    """
    Check if user is a financial user.
    """
    return user_in_group(user, "Financeiro")


def role_required(group_name):
    """
    Restrict access to users from a specific group.
    Superusers always have access.
    """

    def check_user(user):
        return user.is_authenticated and (
            user.is_superuser or user.groups.filter(name=group_name).exists()
        )

    return user_passes_test(
        check_user,
        login_url="accounts:login",
    )


def admin_required(view_func):
    """
    Restrict access to administrators.
    """
    return user_passes_test(
        is_admin,
        login_url="accounts:login",
    )(view_func)


def groups_required(group_names):
    """
    Restrict access to users that belong to at least one allowed group.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")

            if user_in_any_group(request.user, group_names):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "Você não tem permissão para acessar esta área.",
            )

            return redirect("accounts:dashboard")

        return wrapper

    return decorator
