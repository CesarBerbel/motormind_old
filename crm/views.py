from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import user_passes_permission

from .forms import (
    CampaignAudienceForm,
    CampaignForm,
    CustomerInteractionForm,
    CustomerOpportunityForm,
    CustomerReminderForm,
)
from .models import (
    Campaign,
    CampaignAudience,
    CustomerInteraction,
    CustomerOpportunity,
    CustomerReminder,
)
from .permissions import can_manage_crm, can_manage_crm_campaigns, can_view_crm
from .selectors import get_crm_dashboard_data, get_inactive_customers
from .services import create_interaction, mark_reminder_done


@login_required
@user_passes_permission(can_view_crm)
def crm_dashboard_view(request):
    return render(request, "crm/dashboard.html", get_crm_dashboard_data())


@login_required
@user_passes_permission(can_view_crm)
def interaction_list_view(request):
    search = request.GET.get("search", "")
    interactions = CustomerInteraction.objects.select_related(
        "customer", "vehicle", "service_order", "responsible_user"
    )
    if search:
        interactions = interactions.filter(
            Q(customer__name__icontains=search)
            | Q(subject__icontains=search)
            | Q(description__icontains=search)
        )
    return render(
        request,
        "crm/interaction_list.html",
        {"interactions": interactions, "search": search},
    )


@login_required
@user_passes_permission(can_manage_crm)
def interaction_create_view(request):
    initial = {}
    customer_id = request.GET.get("customer")
    service_order_id = request.GET.get("service_order")
    if customer_id:
        initial["customer"] = customer_id
    if service_order_id:
        initial["service_order"] = service_order_id
    if request.method == "POST":
        form = CustomerInteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            create_interaction(
                customer=interaction.customer,
                vehicle=interaction.vehicle,
                service_order=interaction.service_order,
                interaction_type=interaction.interaction_type,
                channel=interaction.channel,
                subject=interaction.subject,
                description=interaction.description,
                responsible_user=request.user,
                next_follow_up_date=interaction.next_follow_up_date,
            )
            messages.success(request, "Interação registrada com sucesso.")
            return redirect("crm:interaction_list")
        messages.error(
            request, "Não foi possível registrar a interação. Verifique os dados."
        )
    else:
        form = CustomerInteractionForm(initial=initial)
    return render(
        request,
        "crm/form.html",
        {
            "form": form,
            "page_title": "Registrar interação",
            "button_text": "Salvar interação",
        },
    )


@login_required
@user_passes_permission(can_view_crm)
def opportunity_list_view(request):
    opportunities = CustomerOpportunity.objects.select_related(
        "customer", "vehicle", "service_order", "responsible_user"
    )
    status = request.GET.get("status", "")
    if status:
        opportunities = opportunities.filter(status=status)
    return render(
        request,
        "crm/opportunity_list.html",
        {
            "opportunities": opportunities,
            "status": status,
            "status_choices": CustomerOpportunity.Status.choices,
        },
    )


@login_required
@user_passes_permission(can_manage_crm)
def opportunity_create_view(request):
    if request.method == "POST":
        form = CustomerOpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.responsible_user = request.user
            opportunity.save()
            messages.success(request, "Oportunidade cadastrada com sucesso.")
            return redirect("crm:opportunity_list")
        messages.error(request, "Não foi possível cadastrar a oportunidade.")
    else:
        form = CustomerOpportunityForm(initial=request.GET.dict())
    return render(
        request,
        "crm/form.html",
        {
            "form": form,
            "page_title": "Cadastrar oportunidade",
            "button_text": "Salvar oportunidade",
        },
    )


@login_required
@user_passes_permission(can_view_crm)
def reminder_list_view(request):
    reminders = CustomerReminder.objects.select_related(
        "customer", "vehicle", "service_order", "responsible_user"
    )
    status = request.GET.get("status", CustomerReminder.Status.PENDING)
    if status:
        reminders = reminders.filter(status=status)
    return render(
        request,
        "crm/reminder_list.html",
        {
            "reminders": reminders,
            "status": status,
            "status_choices": CustomerReminder.Status.choices,
        },
    )


@login_required
@user_passes_permission(can_manage_crm)
def reminder_create_view(request):
    if request.method == "POST":
        form = CustomerReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.responsible_user = request.user
            reminder.save()
            messages.success(request, "Lembrete cadastrado com sucesso.")
            return redirect("crm:reminder_list")
        messages.error(request, "Não foi possível cadastrar o lembrete.")
    else:
        form = CustomerReminderForm(initial=request.GET.dict())
    return render(
        request,
        "crm/form.html",
        {
            "form": form,
            "page_title": "Cadastrar lembrete",
            "button_text": "Salvar lembrete",
        },
    )


@login_required
@user_passes_permission(can_manage_crm)
@require_POST
def reminder_done_view(request, pk):
    reminder = get_object_or_404(CustomerReminder, pk=pk)
    mark_reminder_done(reminder, request.user)
    messages.success(request, "Lembrete concluído com sucesso.")
    return redirect("crm:reminder_list")


@login_required
@user_passes_permission(can_view_crm)
def inactive_customer_list_view(request):
    days = int(request.GET.get("days", 180))
    customers = get_inactive_customers(days=days)
    return render(
        request,
        "crm/inactive_customer_list.html",
        {"customers": customers, "days": days},
    )


@login_required
@user_passes_permission(can_view_crm)
def campaign_list_view(request):
    campaigns = Campaign.objects.select_related("created_by").prefetch_related(
        "audience"
    )
    return render(request, "crm/campaign_list.html", {"campaigns": campaigns})


@login_required
@user_passes_permission(can_manage_crm_campaigns)
def campaign_create_view(request):
    if request.method == "POST":
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()
            messages.success(request, "Campanha criada com sucesso.")
            return redirect("crm:campaign_list")
        messages.error(request, "Não foi possível criar a campanha.")
    else:
        form = CampaignForm()
    return render(
        request,
        "crm/form.html",
        {
            "form": form,
            "page_title": "Criar campanha",
            "button_text": "Salvar campanha",
        },
    )


@login_required
@user_passes_permission(can_manage_crm_campaigns)
def campaign_audience_add_view(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == "POST":
        form = CampaignAudienceForm(request.POST)
        if form.is_valid():
            CampaignAudience.objects.get_or_create(
                campaign=campaign, customer=form.cleaned_data["customer"]
            )
            messages.success(request, "Cliente adicionado ao público da campanha.")
            return redirect("crm:campaign_list")
    else:
        form = CampaignAudienceForm()
    return render(
        request,
        "crm/form.html",
        {
            "form": form,
            "page_title": f"Adicionar público - {campaign.name}",
            "button_text": "Adicionar cliente",
        },
    )
