from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from customers.models import Customer, Vehicle
from financial.models import CashFlowEntry, Expense, Payment, Receivable
from service_orders.models import ServiceOrder, ServiceOrderItem


class SeedRealisticDataCommandTests(TestCase):
    """
    Test seed_realistic_data management command.
    """

    def call_seed_command(self, *args):
        """
        Execute seed_realistic_data command and return output.
        """
        output = StringIO()

        call_command(
            "seed_realistic_data",
            *args,
            stdout=output,
        )

        return output.getvalue()

    def test_command_requires_exactly_one_mode(self):
        """
        Command must require exactly one execution mode.
        """
        output = self.call_seed_command()

        self.assertIn(
            "Choose exactly one option",
            output,
        )

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(ServiceOrder.objects.count(), 0)

    def test_command_rejects_multiple_modes(self):
        """
        Command must reject multiple execution modes at the same time.
        """
        output = self.call_seed_command(
            "--only-seed",
            "--reset-only",
        )

        self.assertIn(
            "Choose exactly one option",
            output,
        )

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(ServiceOrder.objects.count(), 0)

    def test_reset_only_deletes_data_and_recreates_admin(self):
        """
        Reset-only must delete data and recreate only admin user.
        """
        Group.objects.create(name="Financeiro")

        self.call_seed_command(
            "--reset-and-seed",
            "--orders",
            "5",
        )

        self.assertGreater(Customer.objects.count(), 0)
        self.assertGreater(Vehicle.objects.count(), 0)
        self.assertGreater(ServiceOrder.objects.count(), 0)
        self.assertGreater(ServiceOrderItem.objects.count(), 0)
        self.assertGreater(Expense.objects.count(), 0)

        output = self.call_seed_command("--reset-only")

        self.assertIn(
            "Database reset completed",
            output,
        )

        User = get_user_model()

        self.assertEqual(User.objects.count(), 1)

        admin_user = User.objects.get(email="admin@admin.com")

        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.check_password("321654"))

        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(Vehicle.objects.count(), 0)
        self.assertEqual(ServiceOrder.objects.count(), 0)
        self.assertEqual(ServiceOrderItem.objects.count(), 0)
        self.assertEqual(Receivable.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(CashFlowEntry.objects.count(), 0)

    def test_reset_and_seed_recreates_admin_users_by_group_and_business_data(self):
        """
        Reset-and-seed must recreate admin, users by group and business data.
        """
        finance_group = Group.objects.create(name="Financeiro")
        mechanic_group = Group.objects.create(name="Mecanicos")

        output = self.call_seed_command(
            "--reset-and-seed",
            "--orders",
            "8",
        )

        self.assertIn(
            "Realistic seed completed successfully",
            output,
        )

        User = get_user_model()

        admin_user = User.objects.get(email="admin@admin.com")

        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.check_password("321654"))

        self.assertEqual(
            finance_group.user_set.count(),
            5,
        )

        self.assertEqual(
            mechanic_group.user_set.count(),
            5,
        )

        self.assertGreaterEqual(User.objects.count(), 11)

        self.assertGreater(Customer.objects.count(), 0)
        self.assertGreater(Vehicle.objects.count(), 0)
        self.assertEqual(ServiceOrder.objects.count(), 8)
        self.assertGreater(ServiceOrderItem.objects.count(), 0)
        self.assertGreater(Expense.objects.count(), 0)

    def test_only_seed_does_not_delete_existing_users(self):
        """
        Only-seed must keep existing users and only add development data.
        """
        User = get_user_model()

        existing_user = User.objects.create_user(
            email="existing@example.com",
            password="old-password-123",
        )

        group = Group.objects.create(name="Atendimento")

        output = self.call_seed_command(
            "--only-seed",
            "--orders",
            "5",
        )

        self.assertIn(
            "Realistic seed completed successfully",
            output,
        )

        existing_user.refresh_from_db()

        self.assertTrue(existing_user.check_password("old-password-123"))

        self.assertTrue(User.objects.filter(email="existing@example.com").exists())

        self.assertTrue(User.objects.filter(email="admin@admin.com").exists())

        self.assertEqual(
            group.user_set.count(),
            5,
        )

        self.assertGreater(Customer.objects.count(), 0)
        self.assertGreater(Vehicle.objects.count(), 0)
        self.assertEqual(ServiceOrder.objects.count(), 5)
        self.assertGreater(ServiceOrderItem.objects.count(), 0)
        self.assertGreater(Expense.objects.count(), 0)

    def test_group_users_are_created_with_default_password(self):
        """
        Users created by group must use default password 123456.
        """
        group = Group.objects.create(name="Gerencia")

        self.call_seed_command(
            "--reset-and-seed",
            "--orders",
            "3",
        )

        users = group.user_set.all()

        self.assertEqual(users.count(), 5)

        for user in users:
            self.assertTrue(user.check_password("123456"))
            self.assertTrue(user.email.endswith("@motormind.test"))
