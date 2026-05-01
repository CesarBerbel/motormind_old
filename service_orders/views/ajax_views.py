from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from accounts.permissions import groups_required
from customers.models import Vehicle


@login_required
@groups_required(["Administrador", "Atendente"])
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
