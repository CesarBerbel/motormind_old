from django import template

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    """
    Check if the user belongs to a specific group.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()
