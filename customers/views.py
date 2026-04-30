from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import groups_required

from .forms import CustomerForm, VehicleForm
from .models import Customer, Vehicle


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_list_view(request):
    """
    List customers with optional search.
    """
    search = request.GET.get("search", "")

    customers = Customer.objects.all()

    if search:
        customers = customers.filter(
            Q(name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(document__icontains=search)
        )

    return render(
        request,
        "customers/customer_list.html",
        {
            "customers": customers,
            "search": search,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_create_view(request):
    """
    Create a new customer.
    """
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Cliente cadastrado com sucesso.",
            )

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
    """
    Update an existing customer.
    """
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":
        form = CustomerForm(
            request.POST,
            instance=customer,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Cliente atualizado com sucesso.",
            )

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
    """
    Show customer details and linked vehicles.
    """
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    vehicles = customer.vehicles.all()

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "vehicles": vehicles,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def customer_delete_view(request, pk):
    """
    Delete a customer after confirmation.
    """
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":
        customer.delete()

        messages.success(
            request,
            "Cliente excluído com sucesso.",
        )

        return redirect("customers:customer_list")

    return render(
        request,
        "customers/customer_confirm_delete.html",
        {
            "customer": customer,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente", "Mecânico"])
def vehicle_list_view(request):
    """
    List vehicles with optional search.
    """
    search = request.GET.get("search", "")

    vehicles = Vehicle.objects.select_related("customer").all()

    if search:
        vehicles = vehicles.filter(
            Q(plate__icontains=search)
            | Q(brand__icontains=search)
            | Q(model__icontains=search)
            | Q(customer__name__icontains=search)
        )

    return render(
        request,
        "customers/vehicle_list.html",
        {
            "vehicles": vehicles,
            "search": search,
        },
    )


@login_required
@groups_required(["Administrador", "Atendente"])
def vehicle_create_view(request):
    """
    Create a new vehicle.
    """
    if request.method == "POST":
        form = VehicleForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Veículo cadastrado com sucesso.",
            )

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
    """
    Update an existing vehicle.
    """
    vehicle = get_object_or_404(
        Vehicle,
        pk=pk,
    )

    if request.method == "POST":
        form = VehicleForm(
            request.POST,
            instance=vehicle,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Veículo atualizado com sucesso.",
            )

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
    """
    Delete a vehicle after confirmation.
    """
    vehicle = get_object_or_404(
        Vehicle,
        pk=pk,
    )

    if request.method == "POST":
        vehicle.delete()

        messages.success(
            request,
            "Veículo excluído com sucesso.",
        )

        return redirect("customers:vehicle_list")

    return render(
        request,
        "customers/vehicle_confirm_delete.html",
        {
            "vehicle": vehicle,
        },
    )
