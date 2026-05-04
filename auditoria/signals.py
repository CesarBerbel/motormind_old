from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from auditoria.services import log_login_failed, log_login_success, log_logout


@receiver(user_logged_in)
def audit_user_logged_in(sender, request, user, **kwargs):
    log_login_success(sender, request, user, **kwargs)


@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    log_login_failed(sender, credentials, request, **kwargs)


@receiver(user_logged_out)
def audit_user_logged_out(sender, request, user, **kwargs):
    log_logout(sender, request, user, **kwargs)
