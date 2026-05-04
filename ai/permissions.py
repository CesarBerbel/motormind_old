from core.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    MECHANIC_GROUP,
    is_admin,
    user_in_any_group,
)


def can_view_ai(user):
    return user_in_any_group(
        user,
        [ADMIN_GROUP, ATTENDANT_GROUP, MECHANIC_GROUP, FINANCIAL_GROUP],
    )


def can_manage_ai_prompts(user):
    return is_admin(user)


def can_use_ai_for_service_orders(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP, MECHANIC_GROUP])


def can_use_ai_for_messages(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP, FINANCIAL_GROUP])


def can_use_ai_for_crm(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP])


def can_use_ai_for_campaigns(user):
    return is_admin(user)


def can_review_ai_output(user):
    return user_in_any_group(
        user,
        [ADMIN_GROUP, ATTENDANT_GROUP, MECHANIC_GROUP, FINANCIAL_GROUP],
    )


def can_use_ai_case(user, use_case):
    service_order_cases = {
        "service_order_description",
        "technical_diagnosis",
        "technical_report",
    }
    message_cases = {"customer_message"}
    crm_cases = {"crm_analysis", "customer_history_summary"}
    campaign_cases = {"campaign_suggestion"}

    if use_case in service_order_cases:
        return can_use_ai_for_service_orders(user)
    if use_case in message_cases:
        return can_use_ai_for_messages(user)
    if use_case in crm_cases:
        return can_use_ai_for_crm(user)
    if use_case in campaign_cases:
        return can_use_ai_for_campaigns(user)
    return can_view_ai(user)
