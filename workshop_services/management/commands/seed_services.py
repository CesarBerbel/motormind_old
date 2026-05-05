from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopService,
)

SERVICES = [
    {
        "code": "TROCA_OLEO",
        "name": "Troca de óleo",
        "category": "Manutenção preventiva",
        "description": "Substituição do óleo do motor conforme especificação do veículo.",
        "default_price": Decimal("120.00"),
        "estimated_minutes": 40,
    },
    {
        "code": "FILTRO_OLEO",
        "name": "Troca de filtro de óleo",
        "category": "Manutenção preventiva",
        "description": "Substituição do filtro de óleo do motor.",
        "default_price": Decimal("40.00"),
        "estimated_minutes": 15,
    },
    {
        "code": "FILTRO_AR",
        "name": "Troca de filtro de ar",
        "category": "Manutenção preventiva",
        "description": "Substituição do filtro de ar do motor.",
        "default_price": Decimal("50.00"),
        "estimated_minutes": 15,
    },
    {
        "code": "FILTRO_COMBUSTIVEL",
        "name": "Troca de filtro de combustível",
        "category": "Manutenção preventiva",
        "description": "Substituição do filtro de combustível.",
        "default_price": Decimal("60.00"),
        "estimated_minutes": 25,
    },
    {
        "code": "ALINHAMENTO",
        "name": "Alinhamento",
        "category": "Rodas e pneus",
        "description": "Alinhamento da direção e geometria básica.",
        "default_price": Decimal("80.00"),
        "estimated_minutes": 40,
    },
    {
        "code": "BALANCEAMENTO",
        "name": "Balanceamento",
        "category": "Rodas e pneus",
        "description": "Balanceamento das rodas.",
        "default_price": Decimal("60.00"),
        "estimated_minutes": 40,
    },
    {
        "code": "DIAGNOSTICO_ELETRONICO",
        "name": "Diagnóstico eletrônico",
        "category": "Diagnóstico",
        "description": "Diagnóstico eletrônico com equipamento scanner.",
        "default_price": Decimal("150.00"),
        "estimated_minutes": 60,
    },
    {
        "code": "SCANNER_AUTOMOTIVO",
        "name": "Scanner automotivo",
        "category": "Diagnóstico",
        "description": "Leitura de falhas e parâmetros por scanner automotivo.",
        "default_price": Decimal("100.00"),
        "estimated_minutes": 40,
    },
    {
        "code": "REVISAO_FREIOS",
        "name": "Revisão de freios",
        "category": "Freios",
        "description": "Inspeção do sistema de freios.",
        "default_price": Decimal("120.00"),
        "estimated_minutes": 60,
    },
    {
        "code": "TROCA_PASTILHA_FREIO",
        "name": "Troca de pastilha de freio",
        "category": "Freios",
        "description": "Substituição das pastilhas de freio.",
        "default_price": Decimal("150.00"),
        "estimated_minutes": 80,
    },
    {
        "code": "TROCA_DISCO_FREIO",
        "name": "Troca de disco de freio",
        "category": "Freios",
        "description": "Substituição dos discos de freio.",
        "default_price": Decimal("200.00"),
        "estimated_minutes": 100,
    },
    {
        "code": "REVISAO_SUSPENSAO",
        "name": "Revisão de suspensão",
        "category": "Suspensão",
        "description": "Inspeção de amortecedores, buchas, pivôs, bandejas e terminais.",
        "default_price": Decimal("180.00"),
        "estimated_minutes": 70,
    },
    {
        "code": "TROCA_AMORTECEDOR",
        "name": "Troca de amortecedor",
        "category": "Suspensão",
        "description": "Substituição de amortecedor.",
        "default_price": Decimal("250.00"),
        "estimated_minutes": 120,
    },
    {
        "code": "HIGIENIZACAO_AR",
        "name": "Higienização de ar-condicionado",
        "category": "Ar-condicionado",
        "description": "Higienização do sistema de ar-condicionado.",
        "default_price": Decimal("120.00"),
        "estimated_minutes": 50,
    },
    {
        "code": "RECARGA_AR",
        "name": "Recarga de ar-condicionado",
        "category": "Ar-condicionado",
        "description": "Recarga de gás do sistema de ar-condicionado.",
        "default_price": Decimal("200.00"),
        "estimated_minutes": 70,
    },
    {
        "code": "TROCA_BATERIA",
        "name": "Troca de bateria",
        "category": "Elétrica",
        "description": "Substituição da bateria do veículo.",
        "default_price": Decimal("50.00"),
        "estimated_minutes": 20,
    },
    {
        "code": "REVISAO_COMPLETA_SERVICO",
        "name": "Revisão completa",
        "category": "Manutenção preventiva",
        "description": "Revisão geral preventiva do veículo.",
        "default_price": Decimal("300.00"),
        "estimated_minutes": 180,
    },
]


COMBOS = [
    {
        "code": "COMBO_REVISAO_BASICA",
        "name": "Revisão básica",
        "description": "Pacote básico de manutenção preventiva.",
        "discount_amount": Decimal("30.00"),
        "items": [
            "TROCA_OLEO",
            "FILTRO_OLEO",
            "FILTRO_AR",
        ],
    },
    {
        "code": "COMBO_REVISAO_COMPLETA",
        "name": "Revisão completa",
        "description": "Pacote completo com manutenção preventiva, scanner, alinhamento e balanceamento.",
        "discount_amount": Decimal("100.00"),
        "items": [
            "TROCA_OLEO",
            "FILTRO_OLEO",
            "FILTRO_AR",
            "DIAGNOSTICO_ELETRONICO",
            "ALINHAMENTO",
            "BALANCEAMENTO",
        ],
    },
    {
        "code": "COMBO_FREIOS",
        "name": "Pacote freios",
        "description": "Revisão e manutenção básica do sistema de freios.",
        "discount_amount": Decimal("20.00"),
        "items": [
            "REVISAO_FREIOS",
            "TROCA_PASTILHA_FREIO",
        ],
    },
    {
        "code": "COMBO_SUSPENSAO",
        "name": "Pacote suspensão",
        "description": "Revisão e manutenção básica da suspensão.",
        "discount_amount": Decimal("30.00"),
        "items": [
            "REVISAO_SUSPENSAO",
            "TROCA_AMORTECEDOR",
        ],
    },
    {
        "code": "COMBO_AR_CONDICIONADO",
        "name": "Pacote ar-condicionado",
        "description": "Higienização e recarga do sistema de ar-condicionado.",
        "discount_amount": Decimal("40.00"),
        "items": [
            "HIGIENIZACAO_AR",
            "RECARGA_AR",
        ],
    },
    {
        "code": "COMBO_PRE_VIAGEM",
        "name": "Pré-viagem",
        "description": "Checklist preventivo antes de viagens.",
        "discount_amount": Decimal("100.00"),
        "items": [
            "REVISAO_COMPLETA_SERVICO",
            "REVISAO_FREIOS",
            "REVISAO_SUSPENSAO",
        ],
    },
]


class Command(BaseCommand):
    help = "Cria serviços e combos padrão para oficina mecânica."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Criando serviços...")

        services_by_code = {}

        for data in SERVICES:
            service, created = WorkshopService.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "category": data["category"],
                    "description": data["description"],
                    "default_price": data["default_price"],
                    "estimated_minutes": data["estimated_minutes"],
                    "is_active": True,
                },
            )
            services_by_code[service.code] = service

            status = "criado" if created else "atualizado"
            self.stdout.write(f" - {service.name} ({status})")

        self.stdout.write("Criando combos...")

        for data in COMBOS:
            combo, created = ServiceCombo.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "discount_amount": data["discount_amount"],
                    "is_active": True,
                },
            )

            for service_code in data["items"]:
                service = services_by_code[service_code]

                ServiceComboItem.objects.update_or_create(
                    combo=combo,
                    service=service,
                    defaults={
                        "quantity": Decimal("1.00"),
                        "unit_price": service.default_price,
                    },
                )

            status = "criado" if created else "atualizado"
            self.stdout.write(f" - {combo.name} ({status})")

        self.stdout.write(
            self.style.SUCCESS("Seed de serviços e combos concluído com sucesso.")
        )
