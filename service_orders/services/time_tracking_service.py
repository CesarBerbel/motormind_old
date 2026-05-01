from django.utils import timezone

from service_orders.models import ServiceOrder, ServiceOrderTimeEntry


def can_start_time_entry(service_order):
    """
    Check if a service order can receive a new time entry.
    """
    return service_order.status != ServiceOrder.Status.CANCELED


def mechanic_has_open_time_entry(service_order, mechanic):
    """
    Check if the mechanic already has an open time entry for the service order.
    """
    return ServiceOrderTimeEntry.objects.filter(
        service_order=service_order,
        mechanic=mechanic,
        ended_at__isnull=True,
    ).exists()


def start_time_entry(service_order, mechanic):
    """
    Start a new time entry for a mechanic.
    """
    return ServiceOrderTimeEntry.objects.create(
        service_order=service_order,
        mechanic=mechanic,
        started_at=timezone.now(),
    )


def finish_time_entry_from_form(form):
    """
    Finish an open time entry using a valid form.
    """
    time_entry = form.save(commit=False)
    time_entry.ended_at = timezone.now()
    time_entry.save()

    return time_entry
