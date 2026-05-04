from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.exceptions import DomainError
from core.permissions import (
    can_manage_messages,
    can_send_messages,
    can_view_messages,
    user_passes_permission,
)
from mensagens.preview_forms import MessagePreviewForm
from mensagens.template_renderer import (
    extract_template_variables,
    get_missing_variables,
    render_message_text,
)

from .forms import ManualMessageForm, MessageTemplateForm, QueueFilterForm
from .models import MessageQueue, MessageTemplate
from .selectors import (
    get_logs_for_list,
    get_message_dashboard_data,
    get_message_variables_for_help,
    get_queue_for_list,
    get_templates_for_list,
)
from .services import enqueue_message, process_queue_message


@login_required
@user_passes_permission(can_view_messages)
def dashboard(request):
    return render(request, "mensagens/dashboard.html", get_message_dashboard_data())


@login_required
@user_passes_permission(can_view_messages)
def template_list(request):
    search = request.GET.get("q", "").strip()
    channel = request.GET.get("channel", "").strip()
    return render(
        request,
        "mensagens/template_list.html",
        {
            "templates": get_templates_for_list(search=search, channel=channel),
            "filters": {"q": search, "channel": channel},
        },
    )


@login_required
@user_passes_permission(can_manage_messages)
def template_create(request):
    if request.method == "POST":
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Template criado com sucesso.")
            return redirect("mensagens:template_list")
    else:
        form = MessageTemplateForm()
    return render(
        request,
        "mensagens/template_form.html",
        {"form": form, "title": "Novo template"},
    )


@login_required
@user_passes_permission(can_manage_messages)
def template_update(request, pk):
    template = get_object_or_404(MessageTemplate, pk=pk)
    if request.method == "POST":
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Template atualizado com sucesso.")
            return redirect("mensagens:template_list")
    else:
        form = MessageTemplateForm(instance=template)
    return render(
        request,
        "mensagens/template_form.html",
        {"form": form, "title": "Editar template"},
    )


@login_required
@user_passes_permission(can_view_messages)
def variable_help(request):
    context = get_message_variables_for_help()
    return render(request, "mensagens/variable_help.html", context)


@login_required
@user_passes_permission(can_send_messages)
def manual_message_create(request):
    if request.method == "POST":
        form = ManualMessageForm(request.POST)
        if form.is_valid():
            try:
                enqueue_message(created_by=request.user, **form.cleaned_data)
            except DomainError as exc:
                messages.error(request, exc.message)
            else:
                messages.success(request, "Mensagem adicionada à fila com sucesso.")
                return redirect("mensagens:queue_list")
    else:
        form = ManualMessageForm()
    return render(request, "mensagens/manual_message_form.html", {"form": form})


@login_required
@user_passes_permission(can_view_messages)
def queue_list(request):
    form = QueueFilterForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}
    return render(
        request,
        "mensagens/queue_list.html",
        {"form": form, "queue_messages": get_queue_for_list(**filters)},
    )


@login_required
@user_passes_permission(can_send_messages)
def queue_process(request, pk):
    queue_message = get_object_or_404(MessageQueue, pk=pk)
    if request.method == "POST":
        try:
            process_queue_message(queue_message)
        except Exception as exc:
            messages.error(request, f"Falha ao processar mensagem: {exc}")
        else:
            messages.success(request, "Mensagem processada com sucesso.")
    return redirect("mensagens:queue_list")


@login_required
@user_passes_permission(can_view_messages)
def log_list(request):
    form = QueueFilterForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}
    return render(
        request,
        "mensagens/log_list.html",
        {"form": form, "logs": get_logs_for_list(**filters)},
    )


message_variables_view = variable_help


@login_required
def message_preview_view(request):
    preview = None
    required_variables = []
    missing_variables = []

    if request.method == "POST":
        form = MessagePreviewForm(request.POST)

        if form.is_valid():
            template = form.cleaned_data["template"]
            variables = form.cleaned_data["variables"]

            subject = template.subject or ""
            body = template.body or ""

            required_variables = sorted(
                set(
                    extract_template_variables(subject)
                    + extract_template_variables(body)
                )
            )

            missing_variables = sorted(
                set(
                    get_missing_variables(subject, variables)
                    + get_missing_variables(body, variables)
                )
            )

            preview = {
                "template": template,
                "subject": render_message_text(subject, variables),
                "body": render_message_text(body, variables),
                "variables": variables,
            }

    else:
        form = MessagePreviewForm()

    return render(
        request,
        "mensagens/message_preview.html",
        {
            "form": form,
            "preview": preview,
            "required_variables": required_variables,
            "missing_variables": missing_variables,
        },
    )
