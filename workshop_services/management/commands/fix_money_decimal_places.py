from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand

from service_orders.models import ServiceOrder, ServiceOrderItem
from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopService,
    WorkshopServicePart,
)

Q = Decimal("0.01")


def q(value, default=Decimal("0.00")):
    if value in (None, ""):
        return default
    return Decimal(str(value)).quantize(Q, rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Normaliza valores monetários e quantidades para 2 casas decimais."

    def handle(self, *args, **options):
        for obj in ServiceOrder.objects.all():
            obj.labor_cost = q(obj.labor_cost)
            obj.parts_cost = q(obj.parts_cost)
            obj.discount = q(obj.discount)
            obj.save(
                update_fields=["labor_cost", "parts_cost", "discount", "updated_at"]
            )

        for obj in ServiceOrderItem.objects.all():
            obj.quantity = q(obj.quantity, Decimal("1.00"))
            obj.unit_price = q(obj.unit_price)
            obj.save(update_fields=["quantity", "unit_price", "updated_at"])

        for obj in WorkshopService.objects.all():
            obj.default_price = q(obj.default_price)
            obj.save(update_fields=["default_price", "updated_at"])

        for obj in WorkshopServicePart.objects.all():
            obj.quantity = q(obj.quantity, Decimal("1.00"))
            if obj.unit_price is not None:
                obj.unit_price = q(obj.unit_price)
                obj.save(update_fields=["quantity", "unit_price", "updated_at"])
            else:
                obj.save(update_fields=["quantity", "updated_at"])

        for obj in ServiceCombo.objects.all():
            obj.discount_amount = q(obj.discount_amount)
            obj.save(update_fields=["discount_amount", "updated_at"])

        for obj in ServiceComboItem.objects.all():
            obj.quantity = q(obj.quantity, Decimal("1.00"))
            obj.unit_price = q(obj.unit_price)
            obj.save(update_fields=["quantity", "unit_price", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Valores normalizados com sucesso."))
