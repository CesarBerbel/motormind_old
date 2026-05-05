from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import groups_required

from .forms import CustomerForm, VehicleForm
from .models import Customer, Vehicle

try:
    from crm.selectors import get_customer_crm_summary
except ImportError:
    get_customer_crm_summary = None


def _apply_customer_filters(queryset, search, status):
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(document__icontains=search)
            | Q(zip_code__icontains=search)
            | Q(street__icontains=search)
            | Q(neighborhood__icontains=search)
            | Q(city__icontains=search)
            | Q(state__icontains=search)
        )

    if status == "ativos":
        queryset = queryset.filter(deleted_at__isnull=True, is_active=True)
    elif status == "inativos":
        queryset = queryset.filter(Q(deleted_at__isnull=False) | Q(is_active=False))

    return queryset


def _apply_vehicle_filters(queryset, search, status):
    if search:
        queryset = queryset.filter(
            Q(plate__icontains=search)
            | Q(brand__icontains=search)
            | Q(model__icontains=search)
            | Q(customer__name__icontains=search)
        )

    if status == "ativos":
        queryset = queryset.filter(deleted_at__isnull=True, is_active=True)
    elif status == "inativos":
        queryset = queryset.filter(Q(deleted_at__isnull=False) | Q(is_active=False))

    return queryset


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_list_view(request):
    """List customers with optional search and status filter."""
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "ativos")

    base_queryset = (
        Customer.all_objects.all() if status != "ativos" else Customer.objects.all()
    )
    customers = _apply_customer_filters(base_queryset, search, status)

    return render(
        request,
        "customers/customer_list.html",
        {
            "customers": customers,
            "search": search,
            "status": status,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_create_view(request):
    """Create a new customer."""
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Cliente cadastrado com sucesso.")
            return redirect("customers:customer_list")

        messages.error(
            request,
            "Não foi possível cadastrar o cliente. Verifique os dados informados.",
        )
    else:
        form = CustomerForm()

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "page_title": "Cadastrar cliente",
            "button_text": "Salvar cliente",
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_update_view(request, pk):
    """Update an existing customer, including inactive records."""
    customer = get_object_or_404(Customer.all_objects, pk=pk)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso.")
            return redirect("customers:customer_detail", pk=customer.pk)

        messages.error(
            request,
            "Não foi possível atualizar o cliente. Verifique os dados informados.",
        )
    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "page_title": "Editar cliente",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_detail_view(request, pk):
    """Show customer details and linked vehicles."""
    customer = get_object_or_404(Customer.all_objects, pk=pk)
    vehicles = customer.vehicles.all()
    crm_summary = (
        get_customer_crm_summary(customer) if get_customer_crm_summary else None
    )

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "vehicles": vehicles,
            "crm_summary": crm_summary,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_delete_view(request, pk):
    """Deactivate a customer with soft delete after confirmation."""
    customer = get_object_or_404(Customer.objects, pk=pk)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "Cliente inativado com sucesso.")
        return redirect("customers:customer_list")

    return render(
        request,
        "customers/customer_confirm_delete.html",
        {"customer": customer},
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_restore_view(request, pk):
    """Restore a customer previously removed with soft delete."""
    customer = get_object_or_404(Customer.all_objects, pk=pk)

    if request.method == "POST":
        if customer.is_deleted or not customer.is_active:
            customer.restore()
            messages.success(request, "Cliente restaurado com sucesso.")
        else:
            messages.info(request, "Este cliente já está ativo.")

        return redirect("customers:customer_detail", pk=customer.pk)

    return render(
        request,
        "customers/customer_restore_confirm.html",
        {"customer": customer},
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico"])
def vehicle_list_view(request):
    """List vehicles with optional search and status filter."""
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "ativos")

    base_queryset = (
        Vehicle.all_objects.select_related("customer")
        if status != "ativos"
        else Vehicle.objects.select_related("customer")
    )
    vehicles = _apply_vehicle_filters(base_queryset, search, status)

    return render(
        request,
        "customers/vehicle_list.html",
        {
            "vehicles": vehicles,
            "search": search,
            "status": status,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicle_create_view(request):
    """Create a new vehicle."""
    if request.method == "POST":
        form = VehicleForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Veículo cadastrado com sucesso.")
            return redirect("customers:vehicle_list")

        messages.error(
            request,
            "Não foi possível cadastrar o veículo. Verifique os dados informados.",
        )
    else:
        form = VehicleForm()

    return render(
        request,
        "customers/vehicle_form.html",
        {
            "form": form,
            "page_title": "Cadastrar veículo",
            "button_text": "Salvar veículo",
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicle_update_view(request, pk):
    """Update an existing vehicle, including inactive records."""
    vehicle = get_object_or_404(Vehicle.all_objects, pk=pk)

    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)

        if form.is_valid():
            form.save()
            messages.success(request, "Veículo atualizado com sucesso.")
            return redirect("customers:vehicle_list")

        messages.error(
            request,
            "Não foi possível atualizar o veículo. Verifique os dados informados.",
        )
    else:
        form = VehicleForm(instance=vehicle)

    return render(
        request,
        "customers/vehicle_form.html",
        {
            "form": form,
            "page_title": "Editar veículo",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicle_delete_view(request, pk):
    """Deactivate a vehicle with soft delete after confirmation."""
    vehicle = get_object_or_404(Vehicle.objects, pk=pk)

    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "Veículo inativado com sucesso.")
        return redirect("customers:vehicle_list")

    return render(
        request,
        "customers/vehicle_confirm_delete.html",
        {"vehicle": vehicle},
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicle_restore_view(request, pk):
    """Restore a vehicle previously removed with soft delete."""
    vehicle = get_object_or_404(Vehicle.all_objects, pk=pk)

    if request.method == "POST":
        if vehicle.is_deleted or not vehicle.is_active:
            vehicle.restore()
            messages.success(request, "Veículo restaurado com sucesso.")
        else:
            messages.info(request, "Este veículo já está ativo.")

        return redirect("customers:vehicle_list")

    return render(
        request,
        "customers/vehicle_restore_confirm.html",
        {"vehicle": vehicle},
    )
