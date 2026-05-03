from django import template

from core.permissions import user_in_group

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    """
    Check if the user belongs to a specific group.

    This filter is kept in accounts.templatetags.group_tags for compatibility
    with existing templates that use:

        {% load group_tags %}

    The official permission/group rule lives in core.permissions.user_in_group.
    """
    return user_in_group(user, group_name)
