import re

from django.utils import timezone

from .models import (
    MessageLog,
    MessageQueue,
    MessageStatus,
    MessageTemplate,
    MessageVariable,
)

VARIABLE_REGEX = r"\{\{\s*(.*?)\s*\}\}"


def get_message_dashboard_data():
    return {
        "pending_count": MessageQueue.objects.filter(
            status=MessageStatus.PENDING
        ).count(),
        "failed_count": MessageQueue.objects.filter(
            status=MessageStatus.FAILED
        ).count(),
        "sent_today_count": MessageLog.objects.filter(
            status=MessageStatus.SENT, created_at__date=timezone.localdate()
        ).count(),
        "active_templates_count": MessageTemplate.objects.filter(
            is_active=True
        ).count(),
        "recent_logs": MessageLog.objects.select_related(
            "customer", "created_by"
        ).all()[:10],
    }


def get_templates_for_list(*, search="", channel=""):
    qs = MessageTemplate.objects.all()
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
    if channel:
        qs = qs.filter(channel=channel)
    return qs.order_by("channel", "name")


def get_queue_for_list(*, status="", channel=""):
    qs = MessageQueue.objects.select_related("customer", "template", "created_by").all()
    if status:
        qs = qs.filter(status=status)
    if channel:
        qs = qs.filter(channel=channel)
    return qs.order_by("-created_at", "-id")


def get_logs_for_list(*, status="", channel=""):
    qs = MessageLog.objects.select_related("customer", "created_by").all()
    if status:
        qs = qs.filter(status=status)
    if channel:
        qs = qs.filter(channel=channel)
    return qs.order_by("-created_at", "-id")


def get_all_variables():
    """
    Retorna:
    - variáveis cadastradas
    - variáveis detectadas automaticamente nos templates
    """

    registered = list(MessageVariable.objects.filter(is_active=True))

    detected_codes = set()

    templates = MessageTemplate.objects.all()

    for template in templates:
        text = f"{template.subject or ''} {template.body or ''}"

        matches = re.findall(VARIABLE_REGEX, text)

        for match in matches:
            detected_codes.add(match.strip())

    registered_codes = {var.code for var in registered}

    dynamic_variables = []

    for code in detected_codes:
        if code not in registered_codes:
            dynamic_variables.append(
                {
                    "code": code,
                    "description": "Detectada automaticamente",
                    "example": "",
                }
            )

    return {"registered": registered, "detected": dynamic_variables}


def extract_variables_from_text(text):
    if not text:
        return set()

    return set(re.findall(VARIABLE_REGEX, text))


def get_message_variables_for_help():
    registered_variables = list(
        MessageVariable.objects.filter(is_active=True).order_by("category", "code")
    )

    registered_codes = {variable.code for variable in registered_variables}

    template_variables = set()

    templates = MessageTemplate.objects.filter(is_active=True)

    for template in templates:
        template_variables.update(extract_variables_from_text(template.subject))
        template_variables.update(extract_variables_from_text(template.body))

    uncatalogued_variables = sorted(template_variables - registered_codes)

    grouped_variables = {}

    for variable in registered_variables:
        grouped_variables.setdefault(variable.category, []).append(variable)

    return {
        "grouped_variables": grouped_variables,
        "registered_count": len(registered_variables),
        "uncatalogued_variables": uncatalogued_variables,
        "uncatalogued_count": len(uncatalogued_variables),
    }
