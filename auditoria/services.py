from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet
from django.forms.models import model_to_dict

from auditoria.context import get_current_request
from auditoria.models import AuditLog

SENSITIVE_FIELD_NAMES = {
    "password",
    "senha",
    "token",
    "secret",
    "api_key",
    "authorization",
}


def _get_client_ip(request):
    if not request:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def _get_request_user(request):
    if not request:
        return None

    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user

    return None


def _is_sensitive_key(key):
    key_text = str(key).lower()
    return any(sensitive in key_text for sensitive in SENSITIVE_FIELD_NAMES)


def _make_json_safe(value):
    """
    Converte valores comuns do Django/Python para tipos aceitos por JSONField.

    A auditoria recebe snapshots de models e metadados de diversos módulos. Esses
    dados podem conter Decimal, datas, UUIDs, QuerySets, Models ou estruturas
    aninhadas. JSONField não serializa todos esses tipos automaticamente no SQLite
    durante os testes; por isso a normalização precisa acontecer antes do create().
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, (date, time)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Model):
        return {
            "app_label": value._meta.app_label,
            "model": value._meta.model_name,
            "pk": str(value.pk),
            "repr": str(value),
        }

    if isinstance(value, QuerySet):
        return [_make_json_safe(item) for item in value]

    if isinstance(value, dict):
        return _sanitize_dict(value)

    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(item) for item in value]

    return str(value)


def _sanitize_dict(data):
    if not data:
        return data

    sanitized = {}
    for key, value in data.items():
        safe_key = str(key)
        if _is_sensitive_key(safe_key):
            sanitized[safe_key] = "***"
        else:
            sanitized[safe_key] = _make_json_safe(value)
    return sanitized


def serialize_instance(instance, fields=None, exclude=None):
    if instance is None:
        return None

    data = model_to_dict(instance, fields=fields, exclude=exclude)
    return _sanitize_dict(data)


def log_event(
    *,
    action,
    user=None,
    obj=None,
    old_data=None,
    new_data=None,
    metadata=None,
    request=None,
    object_repr="",
):
    """
    Registra um evento de auditoria de forma segura e tolerante.

    A auditoria não deve impedir a operação principal. Por isso, dados recebidos
    de services, views e signals são sanitizados e convertidos para JSON antes da
    persistência.
    """

    request = request or get_current_request()
    resolved_user = user or _get_request_user(request)

    app_label = ""
    model_name = ""
    object_id = ""
    content_type = None

    if obj is not None:
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        object_id = str(obj.pk or "")
        object_repr = object_repr or str(obj)
        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)

    return AuditLog.objects.create(
        user=resolved_user,
        action=action,
        app_label=app_label,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr[:255] if object_repr else "",
        content_type=content_type,
        old_data=_sanitize_dict(old_data),
        new_data=_sanitize_dict(new_data),
        metadata=_sanitize_dict(metadata),
        ip_address=_get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
        path=(request.path if request else ""),
    )


def log_login_success(sender, request, user, **kwargs):
    log_event(action=AuditLog.Action.LOGIN_SUCCESS, user=user, request=request)


def log_login_failed(sender, credentials, request, **kwargs):
    User = get_user_model()
    username_field = User.USERNAME_FIELD
    username = credentials.get(username_field) or credentials.get("username") or ""
    log_event(
        action=AuditLog.Action.LOGIN_FAILED,
        request=request,
        metadata={username_field: username},
    )


def log_logout(sender, request, user, **kwargs):
    log_event(action=AuditLog.Action.LOGOUT, user=user, request=request)
