from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.permissions import can_view_financial, user_passes_permission

from .selectors import (
    get_cash_flow_entries,
    get_cash_flow_summary,
    get_pending_expenses,
    get_pending_receivables,
)


@login_required
@user_passes_permission(can_view_financial)
def dashboard(request):
    """
    Render financial dashboard.
    """
    context = {
        "summary": get_cash_flow_summary(),
        "pending_receivables": get_pending_receivables(),
        "pending_expenses": get_pending_expenses(),
        "cash_flow_entries": get_cash_flow_entries()[:20],
    }

    return render(request, "financial/dashboard.html", context)
