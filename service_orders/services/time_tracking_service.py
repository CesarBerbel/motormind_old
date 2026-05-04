from django.db import transaction
from django.utils import timezone

from core.exceptions import DomainError, PermissionDeniedError
from core.permissions import can_finish_time_entry
from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


@transaction.atomic
def start_time_entry_for_service_order(service_order, mechanic):
    """
    Start a time entry for a mechanic.

    Business rules:
    - canceled service orders cannot receive time entries;
    - the same mechanic cannot have more than one open time entry anywhere;
    - the check is done inside a transaction to keep the operation consistent.
    """
    locked_service_order = ServiceOrder.objects.select_for_update().get(
        pk=service_order.pk,
    )

    if locked_service_order.status == ServiceOrder.Status.CANCELED:
        raise DomainError("Não é possível iniciar tempo em uma ordem cancelada.")

    open_entry = (
        ServiceOrderTimeEntry.objects.select_for_update()
        .filter(
            mechanic=mechanic,
            ended_at__isnull=True,
        )
        .select_related("service_order")
        .first()
    )

    if open_entry:
        if open_entry.service_order_id == locked_service_order.pk:
            raise DomainError(
                "Você já possui um apontamento de tempo em aberto para esta OS."
            )

        raise DomainError(
            "Você já possui um apontamento de tempo em aberto em outra OS. "
            "Finalize o apontamento atual antes de iniciar um novo."
        )

    return ServiceOrderTimeEntry.objects.create(
        service_order=locked_service_order,
        mechanic=mechanic,
        started_at=timezone.now(),
    )


@transaction.atomic
def finish_time_entry(time_entry, finished_by, note=None):
    """
    Finish an open time entry.

    Mechanics can finish only their own entries. Superusers can finish any entry.
    """
    locked_entry = (
        ServiceOrderTimeEntry.objects.select_for_update()
        .select_related("service_order", "mechanic")
        .get(pk=time_entry.pk)
    )

    if not locked_entry.is_open:
        raise DomainError("Este apontamento de tempo já está encerrado.")

    if not can_finish_time_entry(finished_by, locked_entry):
        raise PermissionDeniedError(
            "Você não pode encerrar apontamentos de outro mecânico."
        )

    locked_entry.ended_at = timezone.now()

    if note is not None:
        locked_entry.note = note

    locked_entry.save(
        update_fields=[
            "ended_at",
            "note",
            "updated_at",
        ]
    )

    return locked_entry
