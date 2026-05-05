from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import can_manage_service_order_items, user_passes_permission
from service_orders.models import ServiceOrder
from workshop_services.forms import (
    AddCatalogServiceToOrderForm,
    AddComboToOrderForm,
    ServiceComboForm,
    ServiceComboItemFormSet,
    WorkshopServiceForm,
)
from workshop_services.models import ServiceCombo, WorkshopService
from workshop_services.permissions import (
    can_manage_workshop_services,
    can_view_workshop_services,
)
from workshop_services.selectors import get_combos_for_list, get_services_for_list
from workshop_services.services import add_catalog_service_to_order, add_combo_to_order


@login_required
@user_passes_permission(can_view_workshop_services)
def service_catalog_list_view(request):
    services = get_services_for_list()
    combos = get_combos_for_list()

    return render(
        request,
        "workshop_services/service_catalog_list.html",
        {
            "services": services,
            "combos": combos,
        },
    )


@login_required
@user_passes_permission(can_manage_workshop_services)
def service_create_view(request):
    if request.method == "POST":
        form = WorkshopServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço cadastrado com sucesso.")
            return redirect("workshop_services:service_catalog_list")
        messages.error(request, "Não foi possível cadastrar o serviço.")
    else:
        form = WorkshopServiceForm()

    return render(
        request,
        "workshop_services/service_form.html",
        {
            "form": form,
            "page_title": "Cadastrar serviço",
            "button_text": "Salvar serviço",
        },
    )


@login_required
@user_passes_permission(can_manage_workshop_services)
def service_update_view(request, pk):
    service = get_object_or_404(WorkshopService, pk=pk)

    if request.method == "POST":
        form = WorkshopServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado com sucesso.")
            return redirect("workshop_services:service_catalog_list")
        messages.error(request, "Não foi possível atualizar o serviço.")
    else:
        form = WorkshopServiceForm(instance=service)

    return render(
        request,
        "workshop_services/service_form.html",
        {
            "form": form,
            "page_title": "Editar serviço",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_manage_workshop_services)
def combo_create_view(request):
    combo = ServiceCombo()

    if request.method == "POST":
        form = ServiceComboForm(request.POST, instance=combo)
        formset = ServiceComboItemFormSet(request.POST, instance=combo)

        if form.is_valid() and formset.is_valid():
            combo = form.save()
            formset.instance = combo
            formset.save()
            messages.success(request, "Combo cadastrado com sucesso.")
            return redirect("workshop_services:service_catalog_list")

        messages.error(request, "Não foi possível cadastrar o combo.")
    else:
        form = ServiceComboForm(instance=combo)
        formset = ServiceComboItemFormSet(instance=combo)

    return render(
        request,
        "workshop_services/combo_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": "Cadastrar combo",
            "button_text": "Salvar combo",
        },
    )


@login_required
@user_passes_permission(can_manage_workshop_services)
def combo_update_view(request, pk):
    combo = get_object_or_404(ServiceCombo, pk=pk)

    if request.method == "POST":
        form = ServiceComboForm(request.POST, instance=combo)
        formset = ServiceComboItemFormSet(request.POST, instance=combo)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Combo atualizado com sucesso.")
            return redirect("workshop_services:service_catalog_list")

        messages.error(request, "Não foi possível atualizar o combo.")
    else:
        form = ServiceComboForm(instance=combo)
        formset = ServiceComboItemFormSet(instance=combo)

    return render(
        request,
        "workshop_services/combo_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": "Editar combo",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_manage_service_order_items)
def add_service_to_order_view(request, service_order_pk):
    service_order = get_object_or_404(ServiceOrder, pk=service_order_pk)

    if request.method == "POST":
        form = AddCatalogServiceToOrderForm(request.POST)
        if form.is_valid():
            try:
                add_catalog_service_to_order(
                    service_order=service_order,
                    service=form.cleaned_data["service"],
                    quantity=form.cleaned_data["quantity"],
                    unit_price=form.cleaned_data["unit_price"],
                )
            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, "Não foi possível adicionar o serviço à OS.")
            else:
                messages.success(request, "Serviço adicionado à OS com sucesso.")
                return redirect(
                    "service_orders:service_order_detail", pk=service_order.pk
                )
        else:
            messages.error(request, "Verifique os dados informados.")
    else:
        form = AddCatalogServiceToOrderForm()

    return render(
        request,
        "workshop_services/add_service_to_order_form.html",
        {
            "form": form,
            "service_order": service_order,
            "page_title": "Adicionar serviço à OS",
        },
    )


@login_required
@user_passes_permission(can_manage_service_order_items)
def add_combo_to_order_view(request, service_order_pk):
    service_order = get_object_or_404(ServiceOrder, pk=service_order_pk)

    if request.method == "POST":
        form = AddComboToOrderForm(request.POST)
        if form.is_valid():
            try:
                add_combo_to_order(
                    service_order=service_order,
                    combo=form.cleaned_data["combo"],
                )
            except ValidationError as error:
                form.add_error(None, error)
                messages.error(request, "Não foi possível adicionar o combo à OS.")
            else:
                messages.success(request, "Combo adicionado à OS com sucesso.")
                return redirect(
                    "service_orders:service_order_detail", pk=service_order.pk
                )
        else:
            messages.error(request, "Verifique os dados informados.")
    else:
        form = AddComboToOrderForm()

    return render(
        request,
        "workshop_services/add_combo_to_order_form.html",
        {
            "form": form,
            "service_order": service_order,
            "page_title": "Adicionar combo à OS",
        },
    )
