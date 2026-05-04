from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.forms import CompanySettingsForm
from core.models import CompanySettings
from inventory.selectors import count_low_stock_parts
from service_orders.models import ServiceOrder
from service_orders.selectors import (
    filter_service_orders_by_search,
    get_active_service_orders_for_mechanic,
    get_open_time_entry_for_mechanic,
    get_overdue_service_orders_for_mechanic,
)

from .forms import (
    AdministrativeUserForm,
    CustomUserCreationForm,
    EmailAuthenticationForm,
)
from .permissions import role_required
from .selectors import get_administration_dashboard_data, get_administrative_users


def register_view(request):
    """
    Register a new user and show messages in Portuguese.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Conta criada com sucesso. Bem-vindo ao sistema!",
            )

            return redirect("accounts:dashboard")

        messages.error(
            request,
            "Não foi possível criar a conta. Verifique os dados informados.",
        )

    else:
        form = CustomUserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):
    """
    Authenticate user by email and show messages in Portuguese.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = EmailAuthenticationForm(request.POST)

        if form.is_valid():
            login(request, form.get_user())

            messages.success(
                request,
                "Login realizado com sucesso.",
            )

            return redirect("accounts:dashboard")

        messages.error(
            request,
            "Não foi possível fazer login. Verifique seu email e senha.",
        )

    else:
        form = EmailAuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@login_required
def dashboard_view(request):
    """
    Show main dashboard with operational counters.
    """
    today = timezone.localdate()

    overdue_service_orders_count = (
        ServiceOrder.objects.filter(
            expected_delivery_date__lt=today,
        )
        .exclude(
            status__in=[
                ServiceOrder.Status.FINISHED,
                ServiceOrder.Status.CANCELED,
            ]
        )
        .count()
    )

    assigned_to_me_count = (
        ServiceOrder.objects.filter(
            assigned_mechanic=request.user,
        )
        .exclude(
            status__in=[
                ServiceOrder.Status.FINISHED,
                ServiceOrder.Status.CANCELED,
            ]
        )
        .count()
    )

    low_stock_parts_count = count_low_stock_parts()

    return render(
        request,
        "accounts/dashboard.html",
        {
            "overdue_service_orders_count": overdue_service_orders_count,
            "assigned_to_me_count": assigned_to_me_count,
            "low_stock_parts_count": low_stock_parts_count,
        },
    )


@login_required
@role_required("Administrador")
def admin_area_view(request):
    """
    Show the administrator command center.
    """
    return render(
        request,
        "accounts/admin_area.html",
        get_administration_dashboard_data(),
    )


@login_required
@role_required("Administrador")
def admin_company_settings_view(request):
    """
    Create or update the official workshop data used by MotorMind.
    """
    company_settings = CompanySettings.get_solo()

    if request.method == "POST":
        form = CompanySettingsForm(request.POST, instance=company_settings)

        if form.is_valid():
            form.save()
            messages.success(request, "Dados da oficina atualizados com sucesso.")
            return redirect("accounts:admin_area")
    else:
        form = CompanySettingsForm(instance=company_settings)

    return render(
        request,
        "accounts/admin_company_settings_form.html",
        {
            "form": form,
            "company_settings": company_settings,
        },
    )


@login_required
@role_required("Administrador")
def admin_user_list_view(request):
    """
    List internal users for administrative management.
    """
    search = request.GET.get("search", "").strip()

    return render(
        request,
        "accounts/admin_user_list.html",
        {
            "users": get_administrative_users(search),
            "search": search,
        },
    )


@login_required
@role_required("Administrador")
def admin_user_create_view(request):
    """
    Create a new internal user and assign access profiles.
    """
    if request.method == "POST":
        form = AdministrativeUserForm(request.POST)

        if form.is_valid():
            if not form.cleaned_data.get("password1"):
                form.add_error("password1", "Informe uma senha inicial para o usuário.")
            else:
                user = form.save()
                messages.success(request, f"Usuário {user.email} criado com sucesso.")
                return redirect("accounts:admin_user_list")
    else:
        form = AdministrativeUserForm()

    return render(
        request,
        "accounts/admin_user_form.html",
        {
            "form": form,
            "form_title": "Novo funcionário",
            "submit_label": "Criar funcionário",
        },
    )


@login_required
@role_required("Administrador")
def admin_user_update_view(request, user_id):
    """
    Update an internal user and access profiles.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = get_object_or_404(
        User,
        pk=user_id,
        is_employee=True,
        is_customer=False,
        is_superuser=False,
    )

    if request.method == "POST":
        form = AdministrativeUserForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, f"Usuário {user.email} atualizado com sucesso.")
            return redirect("accounts:admin_user_list")
    else:
        form = AdministrativeUserForm(instance=user)

    return render(
        request,
        "accounts/admin_user_form.html",
        {
            "form": form,
            "managed_user": user,
            "form_title": "Editar usuário",
            "submit_label": "Salvar alterações",
        },
    )


@login_required
@role_required("Atendente")
def attendant_area_view(request):
    """
    Show attendant area.
    """
    return render(
        request,
        "accounts/attendant_area.html",
    )


@login_required
@role_required("Mecânico")
def mechanic_area_view(request):
    """
    Show the mechanic operational area with assigned service orders.

    The mechanic can filter only their own active service orders.
    Finished and canceled orders are intentionally excluded from this panel.
    """
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()

    assigned_orders = get_active_service_orders_for_mechanic(request.user)
    assigned_orders = filter_service_orders_by_search(assigned_orders, search)

    if status:
        assigned_orders = assigned_orders.filter(status=status)

    if priority:
        assigned_orders = assigned_orders.filter(priority=priority)

    active_orders = get_active_service_orders_for_mechanic(request.user)
    overdue_orders = get_overdue_service_orders_for_mechanic(request.user)
    open_time_entry = get_open_time_entry_for_mechanic(request.user)

    return render(
        request,
        "accounts/mechanic_area.html",
        {
            "assigned_orders": assigned_orders,
            "assigned_orders_count": active_orders.count(),
            "filtered_orders_count": assigned_orders.count(),
            "overdue_orders_count": overdue_orders.count(),
            "open_time_entry": open_time_entry,
            "search": search,
            "status": status,
            "priority": priority,
            "status_choices": ServiceOrder.Status.choices,
            "priority_choices": ServiceOrder.Priority.choices,
        },
    )


@login_required
@role_required("Financeiro")
def financial_area_view(request):
    """
    Redirect financial users to the operational financial dashboard.
    """
    return redirect("financial:dashboard")


def logout_view(request):
    """
    Logout current user and redirect to login page.
    """
    logout(request)

    messages.success(
        request,
        "Você saiu do sistema com sucesso.",
    )

    return redirect("accounts:login")
