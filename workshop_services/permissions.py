from core.permissions import ADMIN_GROUP, ATTENDANT_GROUP, user_in_any_group


def can_manage_workshop_services(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP])


def can_view_workshop_services(user):
    return can_manage_workshop_services(user)
