from django.contrib import messages
from django.shortcuts import redirect

from service_orders.models import ServiceOrder


def service_order_is_canceled(service_order):
    """
    Check if service order is canceled.
    """
    return service_order.status == ServiceOrder.Status.CANCELED


def redirect_if_canceled(request, service_order):
    """
    Redirect user when trying to change a canceled service order.
    """
    if service_order_is_canceled(service_order):
        messages.error(
            request,
            "Ordens de serviço canceladas não podem ser alteradas.",
        )

        return redirect(
            "service_orders:service_order_detail",
            pk=service_order.pk,
        )

    return None
