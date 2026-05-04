from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from auditoria.forms import AuditLogFilterForm
from auditoria.models import AuditLog
from auditoria.selectors import get_audit_logs
from core.permissions import can_view_auditoria, user_passes_permission


@login_required
@user_passes_permission(can_view_auditoria)
def audit_log_list(request):
    form = AuditLogFilterForm(request.GET or None)
    logs = get_audit_logs()

    if form.is_valid():
        logs = get_audit_logs(
            action=form.cleaned_data.get("action"),
            app_label=form.cleaned_data.get("app_label"),
            model_name=form.cleaned_data.get("model_name"),
        )

    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "auditoria/audit_log_list.html",
        {
            "form": form,
            "page_obj": page_obj,
        },
    )


@login_required
@user_passes_permission(can_view_auditoria)
def audit_log_detail(request, pk):
    audit_log = get_object_or_404(
        AuditLog.objects.select_related("user", "content_type"),
        pk=pk,
    )

    return render(
        request,
        "auditoria/audit_log_detail.html",
        {"audit_log": audit_log},
    )
