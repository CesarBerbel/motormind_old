from django.core.management.base import BaseCommand

from mensagens.services import process_pending_messages


class Command(BaseCommand):
    help = "Processa mensagens pendentes da fila."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        result = process_pending_messages(limit=options["limit"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Processadas: {result['processed']} | Falhas: {result['failed']}"
            )
        )
