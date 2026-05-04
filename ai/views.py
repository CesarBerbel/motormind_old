from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.exceptions import DomainError
from core.permissions import groups_required

from .forms import AIAssistantForm, AIReviewForm
from .models import AIResponse
from .permissions import can_view_ai
from .selectors import (
    get_ai_usage_summary,
    get_recent_ai_requests,
    get_recent_ai_responses,
)
from .services import CRITICAL_ACTION_WARNING, generate_ai_response, review_ai_response


def _user_can_access_ai(user):
    return can_view_ai(user)


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def dashboard(request):
    context = {
        "summary": get_ai_usage_summary(),
        "recent_requests": get_recent_ai_requests(),
        "recent_responses": get_recent_ai_responses(),
    }
    return render(request, "ai/dashboard.html", context)


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def assistant(request):
    response = None
    form = AIAssistantForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            prompt_template = form.cleaned_data["prompt_template"]
            response = generate_ai_response(
                user=request.user,
                use_case=prompt_template.use_case,
                input_data=form.get_input_data(),
                prompt_template=prompt_template,
            )
            messages.success(request, "Resposta de IA gerada. Revise antes de usar.")
        except DomainError as exc:
            messages.error(request, exc.message)

    return render(
        request,
        "ai/assistant.html",
        {
            "form": form,
            "response": response,
            "critical_action_warning": CRITICAL_ACTION_WARNING,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico", "Financeiro"])
def response_detail(request, pk):
    response = get_object_or_404(
        AIResponse.objects.select_related(
            "request", "request__user", "request__prompt_template"
        ),
        pk=pk,
    )
    form = AIReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            review_ai_response(
                response=response,
                reviewed_by=request.user,
                status=form.cleaned_data["status"],
                edited_output_text=form.cleaned_data.get("edited_output_text", ""),
                notes=form.cleaned_data.get("notes", ""),
            )
            messages.success(request, "Revisão registrada com sucesso.")
            return redirect("ai:response_detail", pk=response.pk)
        except DomainError as exc:
            messages.error(request, exc.message)

    return render(
        request,
        "ai/response_detail.html",
        {
            "response": response,
            "form": form,
            "critical_action_warning": CRITICAL_ACTION_WARNING,
        },
    )
