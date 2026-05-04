from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.models import ServiceOrder

from .models import CustomerInteraction, CustomerOpportunity, CustomerReminder


@transaction.atomic
def create_interaction(
    *,
    customer,
    subject,
    description,
    responsible_user=None,
    interaction_type=CustomerInteraction.InteractionType.INTERNAL,
    channel=CustomerInteraction.Channel.SYSTEM,
    vehicle=None,
    service_order=None,
    next_follow_up_date=None,
):
    interaction = CustomerInteraction.objects.create(
        customer=customer,
        vehicle=vehicle,
        service_order=service_order,
        interaction_type=interaction_type,
        channel=channel,
        subject=subject,
        description=description,
        responsible_user=responsible_user,
        next_follow_up_date=next_follow_up_date,
    )
    log_event(
        action=AuditLog.Action.CREATE,
        user=responsible_user,
        obj=interaction,
        new_data=serialize_instance(interaction),
    )
    return interaction


@transaction.atomic
def create_opportunity_from_service_order(
    *,
    service_order,
    title,
    description="",
    estimated_value=0,
    responsible_user=None,
    expected_close_date=None,
):
    opportunity = CustomerOpportunity.objects.create(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        title=title,
        description=description,
        estimated_value=estimated_value,
        responsible_user=responsible_user,
        expected_close_date=expected_close_date,
    )
    create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=responsible_user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="Oportunidade criada a partir da OS",
        description=f"Oportunidade registrada: {title}",
    )
    log_event(
        action=AuditLog.Action.CREATE,
        user=responsible_user,
        obj=opportunity,
        new_data=serialize_instance(opportunity),
    )
    return opportunity


@transaction.atomic
def create_reminder(
    *,
    customer,
    title,
    due_date,
    notes="",
    responsible_user=None,
    vehicle=None,
    service_order=None,
):
    reminder = CustomerReminder.objects.create(
        customer=customer,
        vehicle=vehicle,
        service_order=service_order,
        title=title,
        notes=notes,
        due_date=due_date,
        responsible_user=responsible_user,
    )
    log_event(
        action=AuditLog.Action.CREATE,
        user=responsible_user,
        obj=reminder,
        new_data=serialize_instance(reminder),
    )
    return reminder


@transaction.atomic
def mark_reminder_done(reminder, user):
    old_data = serialize_instance(reminder)
    reminder.status = CustomerReminder.Status.DONE
    reminder.save(update_fields=["status", "updated_at"])
    log_event(
        action=AuditLog.Action.UPDATE,
        user=user,
        obj=reminder,
        old_data=old_data,
        new_data=serialize_instance(reminder),
    )
    return reminder


def register_service_order_opened(service_order, user):
    return create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="OS aberta",
        description=f"Ordem de serviço #{service_order.pk} aberta: {service_order.title}",
    )


def register_service_order_status_change(service_order, user, old_status, new_status):
    interaction = create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="Status da OS alterado",
        description=f"OS #{service_order.pk}: status alterado de {old_status} para {new_status}.",
    )

    if new_status == ServiceOrder.Status.FINISHED:
        create_reminder(
            customer=service_order.customer,
            vehicle=service_order.vehicle,
            service_order=service_order,
            responsible_user=user,
            title=f"Pós-venda da OS #{service_order.pk}",
            notes="Entrar em contato para confirmar satisfação, dúvidas e possível revisão preventiva.",
            due_date=timezone.localdate() + timedelta(days=3),
        )
    return interaction


def register_service_order_canceled(service_order, user):
    return create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="OS cancelada",
        description=f"Ordem de serviço #{service_order.pk} cancelada.",
    )
