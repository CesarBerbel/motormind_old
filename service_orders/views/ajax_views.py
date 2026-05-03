from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.permissions import can_manage_service_orders, user_passes_permission
from customers.models import Vehicle


@login_required
@user_passes_permission(can_manage_service_orders)
def vehicles_by_customer_view(request):
    """
    Return active vehicles from a selected customer as JSON.
    """
    customer_id = request.GET.get("customer_id")

    vehicles = Vehicle.objects.none()

    if customer_id:
        vehicles = Vehicle.objects.filter(
            customer_id=customer_id,
            is_active=True,
        ).order_by("plate")

    data = [
        {
            "id": vehicle.id,
            "text": f"{vehicle.plate} - {vehicle.brand} {vehicle.model}",
        }
        for vehicle in vehicles
    ]

    return JsonResponse(
        {
            "vehicles": data,
        }
    )
