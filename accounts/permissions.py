"""
Compatibility layer for permission helpers.

The official shared permission rules now live in core.permissions.

This module is kept to avoid breaking existing imports such as:

    from accounts.permissions import can_view_financial

Future modules should import shared permission helpers from core.permissions
whenever possible.
"""

from core.permissions import (
    ADMIN_GROUP,
    ATTENDANT_GROUP,
    FINANCIAL_GROUP,
    MECHANIC_GROUP,
    can_access_customers,
    can_access_inventory,
    can_access_operational_board,
    can_access_productivity_report,
    can_access_vehicles,
    can_access_workshop_agenda,
    can_cancel_service_order,
    can_finish_time_entry,
    can_manage_financial,
    can_manage_inventory,
    can_manage_service_order_items,
    can_manage_service_order_notes,
    can_manage_service_orders,
    can_move_inventory_stock,
    can_track_service_order_time,
    can_update_service_order_technical_data,
    can_view_auditoria,
    can_view_financial,
    can_view_service_orders,
    groups_required,
    is_authenticated_user,
    role_required,
    user_passes_permission,
)
from core.permissions import (
    is_admin as is_admin_user,
)
from core.permissions import (
    is_attendant as is_attendant_user,
)
from core.permissions import (
    is_financial as is_financial_user,
)
from core.permissions import (
    is_mechanic as is_mechanic_user,
)
from core.permissions import (
    user_in_any_group as has_any_group,
)
from core.permissions import (
    user_in_group as has_group,
)

__all__ = [
    "ADMIN_GROUP",
    "ATTENDANT_GROUP",
    "MECHANIC_GROUP",
    "FINANCIAL_GROUP",
    "is_authenticated_user",
    "has_group",
    "has_any_group",
    "is_admin_user",
    "is_attendant_user",
    "is_mechanic_user",
    "is_financial_user",
    "can_access_customers",
    "can_access_vehicles",
    "can_view_service_orders",
    "can_manage_service_orders",
    "can_update_service_order_technical_data",
    "can_cancel_service_order",
    "can_manage_service_order_items",
    "can_manage_service_order_notes",
    "can_access_operational_board",
    "can_access_workshop_agenda",
    "can_track_service_order_time",
    "can_finish_time_entry",
    "can_access_productivity_report",
    "can_access_inventory",
    "can_manage_inventory",
    "can_move_inventory_stock",
    "can_view_financial",
    "can_view_auditoria",
    "can_manage_financial",
    "user_passes_permission",
    "role_required",
    "groups_required",
]
