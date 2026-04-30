from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Create default system groups for the workshop system.
    """

    help = "Cria os grupos padrão do sistema de oficina."

    def handle(self, *args, **options):
        """
        Execute the command to create groups.
        """

        group_names = [
            "Administrador",
            "Atendente",
            "Mecânico",
            "Financeiro",
        ]

        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f"Grupo criado: {group_name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Grupo já existia: {group_name}"))

        administrator_group = Group.objects.get(name="Administrador")
        attendant_group = Group.objects.get(name="Atendente")
        mechanic_group = Group.objects.get(name="Mecânico")
        financial_group = Group.objects.get(name="Financeiro")

        all_permissions = Permission.objects.all()

        administrator_group.permissions.set(all_permissions)

        attendant_group.permissions.clear()
        mechanic_group.permissions.clear()
        financial_group.permissions.clear()

        self.stdout.write(
            self.style.SUCCESS("Permissões do grupo Administrador configuradas.")
        )

        self.stdout.write(self.style.SUCCESS("Grupos padrão configurados com sucesso."))
