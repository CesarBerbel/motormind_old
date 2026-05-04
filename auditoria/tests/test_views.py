from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from auditoria.models import AuditLog


class AuditLogViewTests(TestCase):
    def test_admin_user_can_view_audit_list(self):
        user = get_user_model().objects.create_user(
            email="admin@example.com",
            password="123456",
        )
        group = Group.objects.create(name="Administrador")
        user.groups.add(group)

        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.LOGIN_SUCCESS,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("auditoria:audit_log_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Auditoria")

    def test_financial_user_cannot_view_audit_list(self):
        user = get_user_model().objects.create_user(
            email="financeiro@example.com",
            password="123456",
        )
        group = Group.objects.create(name="Financeiro")
        user.groups.add(group)

        self.client.force_login(user)
        response = self.client.get(reverse("auditoria:audit_log_list"))

        self.assertEqual(response.status_code, 302)
