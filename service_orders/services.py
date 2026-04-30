from .models import ServiceOrderHistory

AUDITED_FIELDS = [
    "assigned_mechanic",
    "title",
    "description",
    "diagnosis",
    "solution",
    "status",
    "labor_cost",
    "parts_cost",
    "discount",
    "expected_delivery_date",
    "finished_at",
]


def normalize_audit_value(value):
    """
    Normalize values before saving them in the audit history.
    """
    if value is None:
        return ""

    return str(value)


def create_service_order_history(
    service_order,
    changed_by,
    old_instance,
):
    """
    Create history records for changed service order fields.
    """
    history_records = []

    for field_name in AUDITED_FIELDS:
        old_value = normalize_audit_value(getattr(old_instance, field_name, None))
        new_value = normalize_audit_value(getattr(service_order, field_name, None))

        if old_value != new_value:
            history_records.append(
                ServiceOrderHistory(
                    service_order=service_order,
                    changed_by=changed_by,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

    if history_records:
        ServiceOrderHistory.objects.bulk_create(history_records)

    return history_records
