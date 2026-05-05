from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Part


APPLICATIONS = [
    {"suffix": "Linha leve flex", "price_factor": Decimal("1.00"), "stock": Decimal("8.00")},
    {"suffix": "Hatch compacto", "price_factor": Decimal("0.95"), "stock": Decimal("10.00")},
    {"suffix": "Sedan compacto", "price_factor": Decimal("1.05"), "stock": Decimal("8.00")},
    {"suffix": "SUV compacto", "price_factor": Decimal("1.18"), "stock": Decimal("6.00")},
    {"suffix": "Pick-up leve", "price_factor": Decimal("1.25"), "stock": Decimal("5.00")},
]


COMPONENTS = [
    {"name": "Filtro de óleo", "category": "Filtros e lubrificação", "cost": "18.00", "sale": "35.00", "minimum": "4.00"},
    {"name": "Filtro de ar do motor", "category": "Filtros e lubrificação", "cost": "22.00", "sale": "45.00", "minimum": "4.00"},
    {"name": "Filtro de combustível", "category": "Filtros e lubrificação", "cost": "28.00", "sale": "58.00", "minimum": "3.00"},
    {"name": "Filtro de cabine", "category": "Filtros e lubrificação", "cost": "25.00", "sale": "55.00", "minimum": "3.00"},
    {"name": "Óleo de motor 5W30 sintético", "category": "Filtros e lubrificação", "cost": "36.00", "sale": "62.00", "minimum": "12.00"},
    {"name": "Óleo de motor 10W40 semissintético", "category": "Filtros e lubrificação", "cost": "28.00", "sale": "50.00", "minimum": "12.00"},
    {"name": "Óleo de motor 15W40 mineral", "category": "Filtros e lubrificação", "cost": "22.00", "sale": "42.00", "minimum": "10.00"},
    {"name": "Aditivo para radiador", "category": "Arrefecimento", "cost": "18.00", "sale": "38.00", "minimum": "8.00"},
    {"name": "Fluido de freio DOT 4", "category": "Freios", "cost": "19.00", "sale": "39.00", "minimum": "6.00"},
    {"name": "Fluido de direção hidráulica", "category": "Direção", "cost": "24.00", "sale": "49.00", "minimum": "4.00"},
    {"name": "Pastilha de freio dianteira", "category": "Freios", "cost": "75.00", "sale": "145.00", "minimum": "3.00"},
    {"name": "Pastilha de freio traseira", "category": "Freios", "cost": "68.00", "sale": "135.00", "minimum": "2.00"},
    {"name": "Disco de freio dianteiro", "category": "Freios", "cost": "110.00", "sale": "220.00", "minimum": "2.00"},
    {"name": "Disco de freio traseiro", "category": "Freios", "cost": "105.00", "sale": "210.00", "minimum": "2.00"},
    {"name": "Tambor de freio", "category": "Freios", "cost": "95.00", "sale": "190.00", "minimum": "1.00"},
    {"name": "Sapata de freio", "category": "Freios", "cost": "60.00", "sale": "125.00", "minimum": "2.00"},
    {"name": "Cilindro de roda", "category": "Freios", "cost": "35.00", "sale": "78.00", "minimum": "2.00"},
    {"name": "Cilindro mestre de freio", "category": "Freios", "cost": "115.00", "sale": "245.00", "minimum": "1.00"},
    {"name": "Flexível de freio dianteiro", "category": "Freios", "cost": "32.00", "sale": "75.00", "minimum": "2.00"},
    {"name": "Sensor ABS", "category": "Freios", "cost": "85.00", "sale": "180.00", "minimum": "1.00"},
    {"name": "Amortecedor dianteiro", "category": "Suspensão", "cost": "180.00", "sale": "360.00", "minimum": "2.00"},
    {"name": "Amortecedor traseiro", "category": "Suspensão", "cost": "160.00", "sale": "320.00", "minimum": "2.00"},
    {"name": "Coxim do amortecedor dianteiro", "category": "Suspensão", "cost": "70.00", "sale": "145.00", "minimum": "2.00"},
    {"name": "Kit batente e coifa dianteiro", "category": "Suspensão", "cost": "55.00", "sale": "120.00", "minimum": "2.00"},
    {"name": "Kit batente e coifa traseiro", "category": "Suspensão", "cost": "48.00", "sale": "105.00", "minimum": "2.00"},
    {"name": "Mola helicoidal dianteira", "category": "Suspensão", "cost": "130.00", "sale": "270.00", "minimum": "1.00"},
    {"name": "Mola helicoidal traseira", "category": "Suspensão", "cost": "120.00", "sale": "250.00", "minimum": "1.00"},
    {"name": "Bandeja de suspensão", "category": "Suspensão", "cost": "145.00", "sale": "310.00", "minimum": "1.00"},
    {"name": "Bucha de bandeja", "category": "Suspensão", "cost": "32.00", "sale": "78.00", "minimum": "3.00"},
    {"name": "Pivô de suspensão", "category": "Suspensão", "cost": "48.00", "sale": "110.00", "minimum": "2.00"},
    {"name": "Terminal de direção", "category": "Direção", "cost": "42.00", "sale": "95.00", "minimum": "2.00"},
    {"name": "Axial de direção", "category": "Direção", "cost": "55.00", "sale": "125.00", "minimum": "2.00"},
    {"name": "Coifa da caixa de direção", "category": "Direção", "cost": "28.00", "sale": "65.00", "minimum": "2.00"},
    {"name": "Barra estabilizadora", "category": "Suspensão", "cost": "95.00", "sale": "205.00", "minimum": "1.00"},
    {"name": "Bieleta da barra estabilizadora", "category": "Suspensão", "cost": "38.00", "sale": "88.00", "minimum": "2.00"},
    {"name": "Bucha da barra estabilizadora", "category": "Suspensão", "cost": "18.00", "sale": "45.00", "minimum": "4.00"},
    {"name": "Rolamento de roda dianteiro", "category": "Rodas e cubos", "cost": "85.00", "sale": "180.00", "minimum": "2.00"},
    {"name": "Rolamento de roda traseiro", "category": "Rodas e cubos", "cost": "80.00", "sale": "170.00", "minimum": "2.00"},
    {"name": "Cubo de roda dianteiro", "category": "Rodas e cubos", "cost": "125.00", "sale": "270.00", "minimum": "1.00"},
    {"name": "Cubo de roda traseiro", "category": "Rodas e cubos", "cost": "120.00", "sale": "260.00", "minimum": "1.00"},
    {"name": "Vela de ignição", "category": "Ignição", "cost": "18.00", "sale": "42.00", "minimum": "12.00"},
    {"name": "Cabo de vela", "category": "Ignição", "cost": "55.00", "sale": "120.00", "minimum": "2.00"},
    {"name": "Bobina de ignição", "category": "Ignição", "cost": "120.00", "sale": "260.00", "minimum": "1.00"},
    {"name": "Sensor de rotação", "category": "Injeção eletrônica", "cost": "65.00", "sale": "145.00", "minimum": "1.00"},
    {"name": "Sensor de fase", "category": "Injeção eletrônica", "cost": "70.00", "sale": "155.00", "minimum": "1.00"},
    {"name": "Sensor MAP", "category": "Injeção eletrônica", "cost": "75.00", "sale": "165.00", "minimum": "1.00"},
    {"name": "Sensor de temperatura", "category": "Injeção eletrônica", "cost": "38.00", "sale": "85.00", "minimum": "2.00"},
    {"name": "Sonda lambda", "category": "Injeção eletrônica", "cost": "115.00", "sale": "245.00", "minimum": "1.00"},
    {"name": "Bico injetor", "category": "Injeção eletrônica", "cost": "135.00", "sale": "285.00", "minimum": "2.00"},
    {"name": "Corpo de borboleta", "category": "Injeção eletrônica", "cost": "290.00", "sale": "620.00", "minimum": "1.00"},
    {"name": "Bomba de combustível", "category": "Alimentação", "cost": "150.00", "sale": "320.00", "minimum": "1.00"},
    {"name": "Refil da bomba de combustível", "category": "Alimentação", "cost": "85.00", "sale": "180.00", "minimum": "2.00"},
    {"name": "Regulador de pressão", "category": "Alimentação", "cost": "75.00", "sale": "165.00", "minimum": "1.00"},
    {"name": "Correia dentada", "category": "Motor", "cost": "75.00", "sale": "160.00", "minimum": "2.00"},
    {"name": "Kit correia dentada", "category": "Motor", "cost": "220.00", "sale": "460.00", "minimum": "1.00"},
    {"name": "Correia do alternador", "category": "Motor", "cost": "45.00", "sale": "98.00", "minimum": "2.00"},
    {"name": "Tensor da correia", "category": "Motor", "cost": "90.00", "sale": "195.00", "minimum": "1.00"},
    {"name": "Polia do virabrequim", "category": "Motor", "cost": "145.00", "sale": "310.00", "minimum": "1.00"},
    {"name": "Coxim do motor", "category": "Motor", "cost": "115.00", "sale": "245.00", "minimum": "1.00"},
    {"name": "Coxim do câmbio", "category": "Câmbio e embreagem", "cost": "105.00", "sale": "225.00", "minimum": "1.00"},
    {"name": "Kit embreagem", "category": "Câmbio e embreagem", "cost": "380.00", "sale": "760.00", "minimum": "1.00"},
    {"name": "Atuador hidráulico de embreagem", "category": "Câmbio e embreagem", "cost": "160.00", "sale": "340.00", "minimum": "1.00"},
    {"name": "Cabo de embreagem", "category": "Câmbio e embreagem", "cost": "65.00", "sale": "145.00", "minimum": "1.00"},
    {"name": "Junta homocinética", "category": "Transmissão", "cost": "110.00", "sale": "240.00", "minimum": "1.00"},
    {"name": "Coifa da homocinética", "category": "Transmissão", "cost": "30.00", "sale": "70.00", "minimum": "2.00"},
    {"name": "Semieixo", "category": "Transmissão", "cost": "260.00", "sale": "560.00", "minimum": "1.00"},
    {"name": "Radiador", "category": "Arrefecimento", "cost": "230.00", "sale": "480.00", "minimum": "1.00"},
    {"name": "Reservatório de expansão", "category": "Arrefecimento", "cost": "65.00", "sale": "145.00", "minimum": "1.00"},
    {"name": "Tampa do reservatório", "category": "Arrefecimento", "cost": "18.00", "sale": "42.00", "minimum": "3.00"},
    {"name": "Válvula termostática", "category": "Arrefecimento", "cost": "65.00", "sale": "145.00", "minimum": "1.00"},
    {"name": "Bomba d'água", "category": "Arrefecimento", "cost": "115.00", "sale": "250.00", "minimum": "1.00"},
    {"name": "Mangueira superior do radiador", "category": "Arrefecimento", "cost": "45.00", "sale": "98.00", "minimum": "1.00"},
    {"name": "Mangueira inferior do radiador", "category": "Arrefecimento", "cost": "48.00", "sale": "105.00", "minimum": "1.00"},
    {"name": "Eletroventilador", "category": "Arrefecimento", "cost": "240.00", "sale": "520.00", "minimum": "1.00"},
    {"name": "Interruptor térmico", "category": "Arrefecimento", "cost": "38.00", "sale": "88.00", "minimum": "1.00"},
    {"name": "Bateria 45Ah", "category": "Elétrica", "cost": "250.00", "sale": "420.00", "minimum": "1.00"},
    {"name": "Bateria 60Ah", "category": "Elétrica", "cost": "320.00", "sale": "540.00", "minimum": "1.00"},
    {"name": "Alternador", "category": "Elétrica", "cost": "380.00", "sale": "780.00", "minimum": "1.00"},
    {"name": "Motor de partida", "category": "Elétrica", "cost": "360.00", "sale": "740.00", "minimum": "1.00"},
    {"name": "Lâmpada H4", "category": "Iluminação", "cost": "18.00", "sale": "42.00", "minimum": "6.00"},
    {"name": "Lâmpada H7", "category": "Iluminação", "cost": "22.00", "sale": "48.00", "minimum": "6.00"},
    {"name": "Lâmpada pingo T10", "category": "Iluminação", "cost": "5.00", "sale": "15.00", "minimum": "10.00"},
    {"name": "Lâmpada de freio", "category": "Iluminação", "cost": "7.00", "sale": "18.00", "minimum": "10.00"},
    {"name": "Palheta dianteira", "category": "Acessórios e acabamento", "cost": "28.00", "sale": "65.00", "minimum": "5.00"},
    {"name": "Palheta traseira", "category": "Acessórios e acabamento", "cost": "22.00", "sale": "52.00", "minimum": "3.00"},
    {"name": "Limpador de para-brisa reservatório", "category": "Acessórios e acabamento", "cost": "12.00", "sale": "28.00", "minimum": "6.00"},
    {"name": "Maçaneta externa", "category": "Acessórios e acabamento", "cost": "45.00", "sale": "98.00", "minimum": "1.00"},
    {"name": "Fechadura da porta", "category": "Acessórios e acabamento", "cost": "80.00", "sale": "175.00", "minimum": "1.00"},
    {"name": "Máquina de vidro", "category": "Acessórios e acabamento", "cost": "130.00", "sale": "280.00", "minimum": "1.00"},
    {"name": "Botão interruptor do vidro", "category": "Elétrica", "cost": "45.00", "sale": "100.00", "minimum": "1.00"},
    {"name": "Compressor do ar-condicionado", "category": "Ar-condicionado", "cost": "780.00", "sale": "1450.00", "minimum": "1.00"},
    {"name": "Filtro secador do ar-condicionado", "category": "Ar-condicionado", "cost": "70.00", "sale": "155.00", "minimum": "1.00"},
    {"name": "Condensador do ar-condicionado", "category": "Ar-condicionado", "cost": "260.00", "sale": "560.00", "minimum": "1.00"},
    {"name": "Válvula de expansão", "category": "Ar-condicionado", "cost": "85.00", "sale": "190.00", "minimum": "1.00"},
    {"name": "Carga de gás R134a", "category": "Ar-condicionado", "cost": "55.00", "sale": "130.00", "minimum": "4.00"},
    {"name": "Silencioso traseiro", "category": "Escapamento", "cost": "160.00", "sale": "340.00", "minimum": "1.00"},
    {"name": "Catalisador", "category": "Escapamento", "cost": "480.00", "sale": "980.00", "minimum": "1.00"},
    {"name": "Abraçadeira de escapamento", "category": "Escapamento", "cost": "15.00", "sale": "38.00", "minimum": "5.00"},
    {"name": "Coxim de escapamento", "category": "Escapamento", "cost": "12.00", "sale": "32.00", "minimum": "6.00"},
    {"name": "Junta da tampa de válvulas", "category": "Motor", "cost": "45.00", "sale": "100.00", "minimum": "1.00"},
]


class Command(BaseCommand):
    help = "Cria um seed idempotente com 500 peças comuns de oficina no estoque."

    def add_arguments(self, parser):
        parser.add_argument(
            "--zero-stock",
            action="store_true",
            help="Cria/atualiza as peças com estoque atual zerado.",
        )
        parser.add_argument(
            "--prefix",
            default="AUTO",
            help="Prefixo do código interno das peças. Padrão: AUTO.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        zero_stock = options["zero_stock"]
        prefix = options["prefix"].strip().upper() or "AUTO"

        created_count = 0
        updated_count = 0
        sequence = 1

        self.stdout.write("Criando seed de 500 peças comuns...")

        for component in COMPONENTS:
            for application in APPLICATIONS:
                internal_code = f"{prefix}-{sequence:04d}"
                cost_price = money(component["cost"], application["price_factor"])
                sale_price = money(component["sale"], application["price_factor"])
                current_stock = Decimal("0.00") if zero_stock else application["stock"]

                part, created = Part.objects.update_or_create(
                    internal_code=internal_code,
                    defaults={
                        "name": f"{component['name']} - {application['suffix']}",
                        "barcode": f"789{sequence:010d}",
                        "brand": "Genérica",
                        "category": component["category"],
                        "unit": "un",
                        "cost_price": cost_price,
                        "sale_price": sale_price,
                        "current_stock": current_stock,
                        "minimum_stock": Decimal(component["minimum"]),
                        "location": build_location(component["category"], sequence),
                        "is_active": True,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                sequence += 1

        total = created_count + updated_count

        self.stdout.write(self.style.SUCCESS("Seed de peças concluído."))
        self.stdout.write(f"Criadas: {created_count}")
        self.stdout.write(f"Atualizadas: {updated_count}")
        self.stdout.write(f"Total processado: {total}")

        if total != 500:
            self.stdout.write(self.style.WARNING(f"Atenção: total esperado era 500, mas foram processadas {total}."))


def money(value, factor):
    return (Decimal(value) * factor).quantize(Decimal("0.01"))


def build_location(category, sequence):
    aisle_by_category = {
        "Filtros e lubrificação": "A",
        "Arrefecimento": "B",
        "Freios": "C",
        "Direção": "D",
        "Suspensão": "E",
        "Rodas e cubos": "F",
        "Ignição": "G",
        "Injeção eletrônica": "H",
        "Alimentação": "I",
        "Motor": "J",
        "Câmbio e embreagem": "K",
        "Transmissão": "L",
        "Elétrica": "M",
        "Iluminação": "N",
        "Acessórios e acabamento": "O",
        "Ar-condicionado": "P",
        "Escapamento": "Q",
    }
    aisle = aisle_by_category.get(category, "Z")
    shelf = ((sequence - 1) % 20) + 1
    return f"Prateleira {aisle}-{shelf:02d}"
