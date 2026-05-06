from workshop_services.models import ServiceCombo, WorkshopService


def get_active_services():
    return (
        WorkshopService.objects.filter(is_active=True)
        .prefetch_related("default_parts", "default_parts__part")
        .order_by("name")
    )


def get_services_for_list():
    return (
        WorkshopService.objects.prefetch_related("default_parts", "default_parts__part")
        .all()
        .order_by("name")
    )


def get_active_combos():
    return (
        ServiceCombo.objects.filter(is_active=True)
        .prefetch_related(
            "items",
            "items__service",
        )
        .order_by("name")
    )


def get_combos_for_list():
    return ServiceCombo.objects.prefetch_related(
        "items",
        "items__service",
    ).order_by("name")
