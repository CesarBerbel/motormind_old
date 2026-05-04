from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from auditoria.models import AuditLog
from auditoria.services import log_event


@override_settings(ROOT_URLCONF="config.urls")
class AuditLogServiceTests(TestCase):
    def test_log_event_masks_sensitive_metadata(self):
        user = get_user_model().objects.create_user(
            email="audit@example.com",
            password="123456",
        )

        log = log_event(
            action=AuditLog.Action.OTHER,
            user=user,
            metadata={"token": "secret-token", "safe": "ok"},
        )

        self.assertEqual(log.user, user)
        self.assertEqual(log.metadata["token"], "***")
        self.assertEqual(log.metadata["safe"], "ok")
