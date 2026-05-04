from core.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    user_in_any_group,
    user_in_group,
)


def can_view_crm(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP, FINANCIAL_GROUP])


def can_manage_crm(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP])


def can_manage_crm_campaigns(user):
    return user_in_group(user, ADMIN_GROUP)
