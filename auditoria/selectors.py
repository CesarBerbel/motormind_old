from auditoria.models import AuditLog


def get_audit_logs(*, user=None, action=None, app_label=None, model_name=None):
    logs = AuditLog.objects.select_related("user", "content_type").all()

    if user:
        logs = logs.filter(user=user)

    if action:
        logs = logs.filter(action=action)

    if app_label:
        logs = logs.filter(app_label=app_label)

    if model_name:
        logs = logs.filter(model_name=model_name)

    return logs
