from workshop_services.models import (
    ServiceCombo,
    WorkshopCatalogAuditLog,
    WorkshopService,
    WorkshopServiceCategory,
)


def get_active_categories():
    return (
        WorkshopServiceCategory.objects.filter(is_active=True)
        .select_related("parent")
        .order_by("parent__name", "name")
    )


def get_categories_for_list():
    return (
        WorkshopServiceCategory.objects.select_related("parent")
        .all()
        .order_by("parent__name", "name")
    )


def get_active_services():
    return (
        WorkshopService.objects.filter(is_active=True)
        .select_related("category", "category__parent")
        .prefetch_related("default_parts", "default_parts__part", "versions")
        .order_by("name")
    )


def get_services_for_list():
    return (
        WorkshopService.objects.select_related("category", "category__parent")
        .prefetch_related("default_parts", "default_parts__part", "versions")
        .all()
        .order_by("name")
    )


def get_active_combos():
    return (
        ServiceCombo.objects.filter(is_active=True)
        .prefetch_related("items", "items__service")
        .order_by("name")
    )


def get_combos_for_list():
    return ServiceCombo.objects.prefetch_related("items", "items__service").order_by(
        "name"
    )


def get_recent_catalog_audit_logs(limit=30):
    return WorkshopCatalogAuditLog.objects.select_related(
        "service", "combo", "category", "changed_by"
    )[:limit]
