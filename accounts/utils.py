def is_admin_user(user):
    """
    Check if user is admin.

    Admin is defined as:
    - superuser
    - OR member of 'Administrador' group
    """
    if not user or not user.is_authenticated:
        return False

    return user.is_superuser or user.groups.filter(name="Administrador").exists()
