$ErrorActionPreference = "Stop"

Write-Host "Aplicando modulo CRM no MotorMind..."

New-Item -ItemType Directory -Force -Path "config/settings" | Out-Null

@'
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)


SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "core",
    "accounts",
    "customers",
    "service_orders",
    "inventory",
    "financial",
    "crm",
    "auditoria",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditoria.middleware.AuditRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}


# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]


LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."
USE_THOUSAND_SEPARATOR = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "accounts.CustomUser"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="MotorMind <no-reply@localhost>",
)

'@ | Set-Content -Encoding UTF8 "config/settings/base.py"

New-Item -ItemType Directory -Force -Path "config" | Out-Null

@'
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path(
        "",
        lambda request: redirect("accounts:login"),
        name="home",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "conta/",
        include("accounts.urls"),
    ),
    path(
        "oficina/",
        include("customers.urls"),
    ),
    path(
        "servicos/",
        include("service_orders.urls"),
    ),
    path("estoque/", include("inventory.urls")),
    path("financial/", include("financial.urls")),
    path("crm/", include("crm.urls")),
    path("auditoria/", include("auditoria.urls")),
]

'@ | Set-Content -Encoding UTF8 "config/urls.py"

New-Item -ItemType Directory -Force -Path "customers" | Out-Null

@'
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
    crm_summary = get_customer_crm_summary(customer) if get_customer_crm_summary else None

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

'@ | Set-Content -Encoding UTF8 "customers/views.py"

New-Item -ItemType Directory -Force -Path "service_orders/services" | Out-Null

@'
from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.models import ServiceOrder
from service_orders.services.history_service import create_service_order_history


def _safe_register_crm_event(function_name, *args, **kwargs):
    """Register CRM side effects without making OS workflow depend on CRM availability."""
    try:
        from crm import services as crm_services
    except ImportError:
        return None

    crm_function = getattr(crm_services, function_name, None)
    if not crm_function:
        return None

    return crm_function(*args, **kwargs)


def apply_finished_at_by_status(service_order):
    """
    Apply finished_at according to service order status.
    """
    if service_order.status == ServiceOrder.Status.FINISHED:
        if not service_order.finished_at:
            service_order.finished_at = timezone.now()
    else:
        service_order.finished_at = None

    return service_order


def create_service_order_from_form(form, created_by):
    """
    Create a service order from a valid form.
    """
    service_order = form.save(commit=False)
    service_order.created_by = created_by
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    log_event(
        action=AuditLog.Action.SERVICE_ORDER_OPENED,
        user=created_by,
        obj=service_order,
        new_data=serialize_instance(service_order),
    )
    _safe_register_crm_event("register_service_order_opened", service_order, created_by)

    return service_order


def update_service_order_from_form(form, changed_by, old_instance):
    """
    Update a service order from a valid administrative form and create audit history.
    """
    service_order = form.save(commit=False)
    old_status = old_instance.status
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )
    if old_status != service_order.status:
        _safe_register_crm_event(
            "register_service_order_status_change",
            service_order,
            changed_by,
            old_status,
            service_order.status,
        )

    return service_order


def update_service_order_technical_from_form(form, changed_by, old_instance):
    """
    Update technical fields from a valid mechanic form and create audit history.
    """
    service_order = form.save(commit=False)
    service_order = apply_finished_at_by_status(service_order)
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.UPDATE,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )

    return service_order


def cancel_service_order(service_order, changed_by):
    """
    Cancel a service order and create audit history.
    """
    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    service_order.status = ServiceOrder.Status.CANCELED
    service_order.finished_at = None
    service_order.save()

    create_service_order_history(
        service_order=service_order,
        changed_by=changed_by,
        old_instance=old_instance,
    )

    log_event(
        action=AuditLog.Action.SERVICE_ORDER_CANCELED,
        user=changed_by,
        obj=service_order,
        old_data=serialize_instance(old_instance),
        new_data=serialize_instance(service_order),
    )
    _safe_register_crm_event("register_service_order_canceled", service_order, changed_by)

    return service_order

'@ | Set-Content -Encoding UTF8 "service_orders/services/service_order_service.py"

New-Item -ItemType Directory -Force -Path "service_orders/views" | Out-Null

@'
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import (
    can_cancel_service_order,
    can_manage_service_orders,
    can_update_service_order_technical_data,
    can_view_service_orders,
    user_passes_permission,
)
from service_orders.forms import (
    ServiceOrderForm,
    ServiceOrderNoteForm,
    ServiceOrderTechnicalForm,
)
from service_orders.models import ServiceOrder
from service_orders.selectors import (
    filter_service_orders_by_search,
    get_all_inventory_parts_for_service_order,
    get_service_order_financial_summary,
    get_service_orders_for_list,
)
from service_orders.services import cancel_service_order as cancel_service_order_service
from service_orders.services import (
    create_service_order_from_form,
    update_service_order_from_form,
    update_service_order_technical_from_form,
)

from .common import redirect_if_canceled

try:
    from crm.selectors import get_service_order_crm_timeline
except ImportError:
    get_service_order_crm_timeline = None


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_list_view(request):
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")

    service_orders = get_service_orders_for_list()
    service_orders = filter_service_orders_by_search(service_orders, search)

    if status:
        service_orders = service_orders.filter(status=status)

    if priority:
        service_orders = service_orders.filter(priority=priority)

    return render(
        request,
        "service_orders/service_order_list.html",
        {
            "service_orders": service_orders,
            "search": search,
            "status": status,
            "priority": priority,
            "status_choices": ServiceOrder.Status.choices,
            "priority_choices": ServiceOrder.Priority.choices,
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_create_view(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST)

        if form.is_valid():
            service_order = create_service_order_from_form(
                form=form,
                created_by=request.user,
            )

            messages.success(request, "Ordem de serviço criada com sucesso.")

            return redirect(
                "service_orders:service_order_detail",
                pk=service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível criar a ordem de serviço. Verifique os dados informados.",
        )
    else:
        form = ServiceOrderForm()

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Criar ordem de serviço",
            "button_text": "Salvar ordem de serviço",
        },
    )


@login_required
@user_passes_permission(can_view_service_orders)
def service_order_detail_view(request, pk):
    service_order = get_object_or_404(
        ServiceOrder.objects.select_related(
            "customer",
            "vehicle",
            "created_by",
            "assigned_mechanic",
        ).prefetch_related(
            "items",
            "notes",
            "history",
            "time_entries",
            "inventory_parts",
        ),
        pk=pk,
    )

    items = service_order.items.all()
    notes = service_order.notes.select_related("created_by").all()
    histories = service_order.history.select_related("changed_by").all()
    time_entries = service_order.time_entries.select_related("mechanic").all()

    open_time_entry = time_entries.filter(
        mechanic=request.user,
        ended_at__isnull=True,
    ).first()

    inventory_parts = get_all_inventory_parts_for_service_order(service_order)
    financial_summary = get_service_order_financial_summary(service_order)
    crm_timeline = get_service_order_crm_timeline(service_order) if get_service_order_crm_timeline else []

    return render(
        request,
        "service_orders/service_order_detail.html",
        {
            "service_order": service_order,
            "items": items,
            "notes": notes,
            "histories": histories,
            "time_entries": time_entries,
            "open_time_entry": open_time_entry,
            "inventory_parts": inventory_parts,
            "inventory_parts_total": financial_summary["inventory_parts_total"],
            "manual_items_total": financial_summary["manual_items_total"],
            "financial_subtotal": financial_summary["gross_total"],
            "financial_total": financial_summary["net_total"],
            "financial_summary": financial_summary,
            "note_form": ServiceOrderNoteForm(),
            "crm_timeline": crm_timeline,
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
def service_order_update_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderForm(request.POST, instance=service_order)

        if form.is_valid():
            updated_service_order = update_service_order_from_form(
                form=form,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(request, "Ordem de serviço atualizada com sucesso.")

            return redirect(
                "service_orders:service_order_detail",
                pk=updated_service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar a ordem de serviço. Verifique os dados informados.",
        )
    else:
        form = ServiceOrderForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Editar ordem de serviço",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_update_service_order_technical_data)
def service_order_technical_update_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    canceled_redirect = redirect_if_canceled(request, service_order)

    if canceled_redirect:
        return canceled_redirect

    old_instance = ServiceOrder.objects.get(pk=service_order.pk)

    if request.method == "POST":
        form = ServiceOrderTechnicalForm(request.POST, instance=service_order)

        if form.is_valid():
            updated_service_order = update_service_order_technical_from_form(
                form=form,
                changed_by=request.user,
                old_instance=old_instance,
            )

            messages.success(request, "Dados técnicos atualizados com sucesso.")

            return redirect(
                "service_orders:service_order_detail",
                pk=updated_service_order.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar os dados técnicos. Verifique os dados informados.",
        )
    else:
        form = ServiceOrderTechnicalForm(instance=service_order)

    return render(
        request,
        "service_orders/service_order_form.html",
        {
            "form": form,
            "page_title": "Atualizar dados técnicos",
            "button_text": "Salvar dados técnicos",
        },
    )


@login_required
@user_passes_permission(can_cancel_service_order)
def service_order_cancel_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    if request.method == "POST":
        canceled_service_order = cancel_service_order_service(
            service_order=service_order,
            changed_by=request.user,
        )

        messages.warning(request, "Ordem de serviço cancelada com sucesso.")

        return redirect(
            "service_orders:service_order_detail",
            pk=canceled_service_order.pk,
        )

    return render(
        request,
        "service_orders/service_order_confirm_cancel.html",
        {
            "service_order": service_order,
        },
    )


@login_required
@user_passes_permission(can_manage_service_orders)
@require_POST
def service_order_quick_status_update_view(request, pk):
    service_order = get_object_or_404(ServiceOrder, pk=pk)

    new_status = request.POST.get("status")
    valid_statuses = dict(ServiceOrder._meta.get_field("status").choices)

    if new_status not in valid_statuses:
        return JsonResponse(
            {
                "ok": False,
                "error": "Status inválido.",
            },
            status=400,
        )

    if service_order.status == ServiceOrder.Status.CANCELED:
        return JsonResponse(
            {
                "ok": False,
                "error": "Ordens canceladas não podem ser alteradas.",
            },
            status=400,
        )

    service_order.status = new_status
    service_order.save(update_fields=["status", "updated_at"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "status": service_order.status,
                "status_label": service_order.get_status_display(),
            }
        )

    messages.success(request, "Status da ordem atualizado com sucesso.")

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("service_orders:service_order_board")

'@ | Set-Content -Encoding UTF8 "service_orders/views/order_views.py"

New-Item -ItemType Directory -Force -Path "templates" | Out-Null

@'
{% load static %}
{% load group_tags %}

<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">

    <title>
        {% block title %}
            Sistema de Oficina
        {% endblock %}
    </title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap is used to create a responsive and professional interface. -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom public styles -->
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    {% block extra_css %}{% endblock %}
</head>

<body class="bg-light">

<div id="messages-container">
    {% if messages %}
        {% for message in messages %}
            <div class="toast-message toast-{{ message.tags }} animate__animated animate__fadeInDown">
                <span>{{ message }}</span>
                <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.remove()"></button>
            </div>
        {% endfor %}
    {% endif %}
</div>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">

        <a class="navbar-brand" href="{% url 'accounts:dashboard' %}">
            Sistema de Oficina
        </a>

        <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#mainNavbar"
            aria-controls="mainNavbar"
            aria-expanded="false"
            aria-label="Abrir menu"
        >
            <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="mainNavbar">

            <ul class="navbar-nav me-auto mb-2 mb-lg-0">

                {% if request.user.is_authenticated %}

                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'accounts:dashboard' %}">
                            Painel
                        </a>
                    </li>

                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'customers:customer_list' %}">
                                Clientes
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" or request.user|has_group:"Mecânico" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'customers:vehicle_list' %}">
                                Veículos
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" or request.user|has_group:"Mecânico" or request.user|has_group:"Financeiro" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'service_orders:service_order_list' %}">
                                Ordens de serviço
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" or request.user|has_group:"Mecânico" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'service_orders:service_order_board' %}">
                                Quadro da oficina
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Administrador" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'accounts:admin_area' %}">
                                Administração
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Atendente" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'accounts:attendant_area' %}">
                                Atendimento
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Mecânico" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'accounts:mechanic_area' %}">
                                Mecânica
                            </a>
                        </li>
                    {% endif %}

                    {% if request.user|has_group:"Financeiro" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'accounts:financial_area' %}">
                                Financeiro
                            </a>
                        </li>
                    {% endif %}

                    <!-- 🔥 NOVO: AGENDA -->
                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" or request.user|has_group:"Mecânico" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'service_orders:workshop_agenda' %}">
                                Agenda
                            </a>
                        </li>
                    {% endif %}                    

                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'service_orders:mechanic_productivity_report' %}">
                                Produtividade
                            </a>
                        </li>
                    {% endif %}

                    {% if user|has_group:"Administrador" or user|has_group:"Atendente" or user|has_group:"Mecânico" or user|has_group:"Financeiro" %}
                        <li class="nav-item">
                            <a class="nav-link {% if 'inventory' in request.path %}active{% endif %}" href="{% url 'inventory:part_list' %}">
                                <i class="bi bi-box-seam"></i> Estoque
                            </a>
                        </li>
                    {% endif %}


                    {% if user|has_group:"Administrador" or user|has_group:"Atendente" or user|has_group:"Financeiro" %}
                        <li class="nav-item">
                            <a class="nav-link {% if '/crm/' in request.path %}active{% endif %}" href="{% url 'crm:dashboard' %}">
                                CRM
                            </a>
                        </li>
                    {% endif %}

                    {% if user|has_group:"Administrador" %}
                        <li class="nav-item">
                            <a class="nav-link {% if 'auditoria' in request.path %}active{% endif %}" href="{% url 'auditoria:audit_log_list' %}">
                                Auditoria
                            </a>
                        </li>
                    {% endif %}

                {% endif %}

            </ul>

            <ul class="navbar-nav ms-auto mb-2 mb-lg-0">

                {% if request.user.is_authenticated %}

                    <li class="nav-item">
                        <span class="navbar-text text-white me-3">
                            {{ request.user.email }}
                        </span>
                    </li>

                    <li class="nav-item">
                        <a class="btn btn-outline-light btn-sm" href="{% url 'accounts:logout' %}">
                            Sair
                        </a>
                    </li>

                {% else %}

                    <li class="nav-item me-2">
                        <a class="btn btn-outline-light btn-sm" href="{% url 'accounts:login' %}">
                            Entrar
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="btn btn-primary btn-sm" href="{% url 'accounts:register' %}">
                            Criar conta
                        </a>
                    </li>

                {% endif %}

            </ul>

        </div>
    </div>
</nav>

<main class="py-4">

    {% block container %}
        <div class="container">
    {% endblock %}   
        
        {% block content %}{% endblock %}


    {% block endcontainer %}
        </div>
    {% endblock %}

</main>

{% block extra_js %}{% endblock %}
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js"></script>

<script>
    $(document).ready(function() {
        console.log("MotorMind: Scripts carregados com sucesso!");

        // --- MÁSCARA DINÂMICA CPF / CNPJ ---
        var docBehavior = function (val) {
            // Remove tudo que não é dígito para contar o tamanho real
            return val.replace(/\D/g, '').length <= 11 ? '000.000.000-009' : '00.000.000/0000-00';
        },
        docOptions = {
            onKeyPress: function(val, e, field, options) {
                field.mask(docBehavior.apply({}, arguments), options);
            },
            clearIfNotMatch: false // Permite que o usuário continue digitando para trocar a máscara
        };

        if ($('#cpf_mask').length) {
            // Inicializa a máscara
            $('#cpf_mask').mask(docBehavior, docOptions);
            console.log("MotorMind: Máscara Dinâmica de Documento aplicada.");
        }

        // --- MÁSCARA DINÂMICA TELEFONE ---
        var phoneBehavior = function (val) {
            return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
        },
        phoneOptions = {
            onKeyPress: function (val, e, field, options) {
                field.mask(phoneBehavior.apply({}, arguments), options);
            }
        };

        if ($('#phone_mask').length) {
            $('#phone_mask').mask(phoneBehavior, phoneOptions);
            console.log("MotorMind: Máscara de Telefone aplicada.");
        }

        // --- AUTO-HIDE MESSAGES ---
        setTimeout(function() {
            $('.toast-message:not(.toast-error)').fadeOut(600);
        }, 3000);
    });
</script>
</body>
</html>
'@ | Set-Content -Encoding UTF8 "templates/base.html"

New-Item -ItemType Directory -Force -Path "templates/customers" | Out-Null

@'
{% extends "base.html" %}
{% load group_tags %}

{% block title %}
    Detalhes do cliente - Sistema de Oficina

{% if crm_summary %}
<div class="card shadow-sm mt-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">CRM do cliente</h2>
            <div class="d-flex gap-2">
                <a href="{% url 'crm:interaction_create' %}?customer={{ customer.pk }}" class="btn btn-sm btn-outline-primary">Registrar interação</a>
                <a href="{% url 'crm:reminder_create' %}?customer={{ customer.pk }}" class="btn btn-sm btn-outline-secondary">Criar lembrete</a>
            </div>
        </div>

        <div class="row g-3">
            <div class="col-lg-6">
                <h3 class="h6">Últimas interações</h3>
                {% for interaction in crm_summary.interactions %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ interaction.subject }}</strong><br>
                        <span class="text-muted small">{{ interaction.interaction_date|date:"d/m/Y H:i" }} · {{ interaction.get_interaction_type_display }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhuma interação registrada.</p>
                {% endfor %}
            </div>
            <div class="col-lg-3">
                <h3 class="h6">Oportunidades abertas</h3>
                {% for opportunity in crm_summary.open_opportunities %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ opportunity.title }}</strong><br>
                        <span class="text-muted small">R$ {{ opportunity.estimated_value }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhuma oportunidade aberta.</p>
                {% endfor %}
            </div>
            <div class="col-lg-3">
                <h3 class="h6">Follow-ups pendentes</h3>
                {% for reminder in crm_summary.pending_reminders %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ reminder.title }}</strong><br>
                        <span class="text-muted small">{{ reminder.due_date|date:"d/m/Y" }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhum follow-up pendente.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endif %}

{% endblock %}

{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h4 mb-1">
            {{ customer.name }}
        </h1>

        <p class="text-muted mb-0">
            Detalhes do cliente e veículos vinculados.
        </p>
    </div>

    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
        <div>
            <a href="{% url 'customers:customer_update' customer.pk %}" class="btn btn-outline-secondary">
                Editar cliente
            </a>

            <a href="{% url 'customers:vehicle_create' %}" class="btn btn-primary">
                Cadastrar veículo
            </a>
        </div>
    {% endif %}
</div>

<div class="row g-3 mb-4">

    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Dados do cliente
                </h2>

                <p><strong>Telefone:</strong> {{ customer.phone }}</p>
                <p><strong>Email:</strong> {{ customer.email|default:"Não informado" }}</p>
                <p><strong>Documento:</strong> {{ customer.document|default:"Não informado" }}</p>
                <p><strong>Endereço:</strong> {{ customer.address|default:"Não informado" }}</p>

                <p class="mb-0">
                    <strong>Situação:</strong>
                    {% if customer.is_active %}
                        <span class="badge text-bg-success">Ativo</span>
                    {% else %}
                        <span class="badge text-bg-secondary">Inativo</span>
                    {% endif %}
                </p>

            </div>
        </div>
    </div>

    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Observações
                </h2>

                <p class="mb-0">
                    {{ customer.notes|default:"Nenhuma observação registrada." }}
                </p>

            </div>
        </div>
    </div>

</div>

<div class="card shadow-sm">
    <div class="card-body">

        <h2 class="h5 mb-3">
            Veículos do cliente
        </h2>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Matrícula/Placa</th>
                        <th>Marca</th>
                        <th>Modelo</th>
                        <th>Ano</th>
                        <th>Quilometragem</th>
                        <th class="text-end">Ações</th>
                    </tr>
                </thead>

                <tbody>
                    {% for vehicle in vehicles %}
                        <tr>
                            <td>{{ vehicle.plate }}</td>
                            <td>{{ vehicle.brand }}</td>
                            <td>{{ vehicle.model }}</td>
                            <td>{{ vehicle.year|default:"-" }}</td>
                            <td>{{ vehicle.mileage|default:"-" }}</td>
                            <td class="text-end">
                                {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                                    <a href="{% url 'customers:vehicle_update' vehicle.pk %}" class="btn btn-sm btn-outline-secondary">
                                        Editar
                                    </a>
                                {% else %}
                                    <span class="text-muted">
                                        Somente visualização
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-4">
                                Nenhum veículo vinculado a este cliente.
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <a href="{% url 'customers:customer_list' %}" class="btn btn-outline-secondary">
            Voltar
        </a>

    </div>
</div>


{% if crm_summary %}
<div class="card shadow-sm mt-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">CRM do cliente</h2>
            <div class="d-flex gap-2">
                <a href="{% url 'crm:interaction_create' %}?customer={{ customer.pk }}" class="btn btn-sm btn-outline-primary">Registrar interação</a>
                <a href="{% url 'crm:reminder_create' %}?customer={{ customer.pk }}" class="btn btn-sm btn-outline-secondary">Criar lembrete</a>
            </div>
        </div>

        <div class="row g-3">
            <div class="col-lg-6">
                <h3 class="h6">Últimas interações</h3>
                {% for interaction in crm_summary.interactions %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ interaction.subject }}</strong><br>
                        <span class="text-muted small">{{ interaction.interaction_date|date:"d/m/Y H:i" }} · {{ interaction.get_interaction_type_display }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhuma interação registrada.</p>
                {% endfor %}
            </div>
            <div class="col-lg-3">
                <h3 class="h6">Oportunidades abertas</h3>
                {% for opportunity in crm_summary.open_opportunities %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ opportunity.title }}</strong><br>
                        <span class="text-muted small">R$ {{ opportunity.estimated_value }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhuma oportunidade aberta.</p>
                {% endfor %}
            </div>
            <div class="col-lg-3">
                <h3 class="h6">Follow-ups pendentes</h3>
                {% for reminder in crm_summary.pending_reminders %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ reminder.title }}</strong><br>
                        <span class="text-muted small">{{ reminder.due_date|date:"d/m/Y" }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted">Nenhum follow-up pendente.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endif %}

{% endblock %}
'@ | Set-Content -Encoding UTF8 "templates/customers/customer_detail.html"

New-Item -ItemType Directory -Force -Path "templates/service_orders" | Out-Null

@'
{% extends "base.html" %}
{% load group_tags %}
{% load core_formatters %}

{% block title %}
    Ordem de serviço #{{ service_order.pk }} - Sistema de Oficina
<div class="card shadow-sm mb-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">CRM vinculado à OS</h2>
            <div class="d-flex gap-2">
                <a href="{% url 'crm:interaction_create' %}?customer={{ service_order.customer.pk }}&service_order={{ service_order.pk }}" class="btn btn-sm btn-outline-primary">Registrar interação</a>
                <a href="{% url 'crm:opportunity_create' %}?customer={{ service_order.customer.pk }}&vehicle={{ service_order.vehicle.pk }}&service_order={{ service_order.pk }}" class="btn btn-sm btn-outline-secondary">Criar oportunidade</a>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-sm table-hover align-middle mb-0">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Canal</th>
                        <th>Assunto</th>
                        <th>Responsável</th>
                    </tr>
                </thead>
                <tbody>
                    {% for interaction in crm_timeline %}
                        <tr>
                            <td>{{ interaction.interaction_date|date:"d/m/Y H:i" }}</td>
                            <td>{{ interaction.get_interaction_type_display }}</td>
                            <td>{{ interaction.get_channel_display }}</td>
                            <td>{{ interaction.subject }}</td>
                            <td>{{ interaction.responsible_user|default:"Sistema" }}</td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-3">Nenhuma interação de CRM vinculada a esta OS.</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

{% endblock %}

{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h4 mb-1">
            Ordem de serviço #{{ service_order.pk }}
        </h1>

        <p class="text-muted mb-0">
            {{ service_order.title }}
        </p>
    </div>

    <div>
        {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
            {% if service_order.status != "canceled" %}
                <a href="{% url 'service_orders:service_order_update' service_order.pk %}" class="btn btn-outline-secondary">
                    Editar
                </a>

                <a href="{% url 'service_orders:service_order_item_add' service_order.pk %}" class="btn btn-primary">
                    Adicionar item
                </a>
            {% endif %}
        {% endif %}

        {% if request.user|has_group:"Administrador" or request.user|has_group:"Mecânico" %}
            {% if service_order.status != "canceled" %}
                <a href="{% url 'service_orders:service_order_technical_update' service_order.pk %}" class="btn btn-outline-warning">
                    Atualizar técnico
                </a>
            {% endif %}
        {% endif %}
    </div>
</div>

<div class="row g-3 mb-4">

    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Dados gerais
                </h2>

                <p><strong>Cliente:</strong> {{ service_order.customer.name }}</p>
                <p><strong>Veículo:</strong> {{ service_order.vehicle.plate }} - {{ service_order.vehicle.brand }} {{ service_order.vehicle.model }}</p>
                <p><strong>Status:</strong> {{ service_order.get_status_display }}</p>

                <p>
                    <strong>Prioridade:</strong>
                    {% if service_order.priority == "high" %}
                        <span class="badge text-bg-danger">Alta</span>
                    {% elif service_order.priority == "medium" %}
                        <span class="badge text-bg-warning">Média</span>
                    {% else %}
                        <span class="badge text-bg-success">Baixa</span>
                    {% endif %}
                </p>

                <p><strong>Criado por:</strong> {{ service_order.created_by.email }}</p>

                <p>
                    <strong>Mecânico responsável:</strong>
                    {% if service_order.assigned_mechanic %}
                        {{ service_order.assigned_mechanic.email }}
                    {% else %}
                        Não definido
                    {% endif %}
                </p>

                <p><strong>Criada em:</strong> {{ service_order.created_at|date:"d/m/Y H:i" }}</p>

                <p class="mb-0">
                    <strong>Previsão de entrega:</strong>
                    {{ service_order.expected_delivery_date|date:"d/m/Y"|default:"Não informada" }}
                </p>

            </div>
        </div>
    </div>

    <div class="card shadow-sm mb-4">
        <div class="card-body">

            <h2 class="h5 mb-3">
                Resumo financeiro
            </h2>

            <div class="table-responsive">
                <table class="table table-sm align-middle">
                    <tbody>
                        <tr>
                            <th>Mão de obra</th>
                            <td class="text-end">
                                {{ service_order.labor_cost|brl }}
                            </td>
                        </tr>

                        <tr>
                            <th>Peças manuais</th>
                            <td class="text-end">
                                {{ service_order.parts_cost|brl }}
                            </td>
                        </tr>

                        <tr>
                            <th>Itens manuais da OS</th>
                            <td class="text-end">
                                {{ manual_items_total|brl }}
                            </td>
                        </tr>

                        <tr>
                            <th>Peças do estoque</th>
                            <td class="text-end">
                                {{ inventory_parts_total|brl }}
                            </td>
                    </tr>

                    <tr>
                        <th>Subtotal</th>
                        <td class="text-end">
                            {{ financial_subtotal|brl }}
                        </td>
                    </tr>

                    <tr>
                        <th>Desconto geral</th>
                        <td class="text-end text-danger">
                            - {{ service_order.discount|brl }}
                        </td>
                    </tr>

                    <tr class="table-dark">
                        <th>Total geral da OS</th>
                        <td class="text-end fw-bold">
                            {{ financial_total|brl }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="alert alert-info mb-0">
            Peças do estoque entram no total apenas quando estão com status
            <strong>Reservada</strong> ou <strong>Usada</strong>.
            Peças <strong>Canceladas</strong> ou <strong>Devolvidas</strong>
            não entram no total.
        </div>

    </div>
</div>

</div>

<div class="row g-3 mb-4">

    <div class="col-md-4">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Problema informado
                </h2>

                <p class="mb-0">
                    {{ service_order.description }}
                </p>

            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Diagnóstico técnico
                </h2>

                <p class="mb-0">
                    {{ service_order.diagnosis|default:"Ainda não informado." }}
                </p>

            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card shadow-sm h-100">
            <div class="card-body">

                <h2 class="h6">
                    Serviço executado
                </h2>

                <p class="mb-0">
                    {{ service_order.solution|default:"Ainda não informado." }}
                </p>

            </div>
        </div>
    </div>

</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">

        <h2 class="h5 mb-3">
            Observações internas
        </h2>

        {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" or request.user|has_group:"Mecânico" %}
            {% if service_order.status != "canceled" %}
                <form method="post" action="{% url 'service_orders:service_order_note_create' service_order.pk %}" class="mb-4">
                    {% csrf_token %}

                    {{ note_form.as_p }}

                    <button type="submit" class="btn btn-primary">
                        Adicionar observação
                    </button>
                </form>
            {% endif %}
        {% endif %}

        <div class="list-group">
            {% for note in notes %}
                <div class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <strong>{{ note.get_note_type_display }}</strong>
                        <small class="text-muted">
                            {{ note.created_at|date:"d/m/Y H:i" }}
                        </small>
                    </div>

                    <p class="mb-1 mt-2">
                        {{ note.text }}
                    </p>

                    <small class="text-muted">
                        Criado por: {{ note.created_by.email }}
                    </small>
                </div>
            {% empty %}
                <div class="text-center text-muted py-3">
                    Nenhuma observação registrada.
                </div>
            {% endfor %}
        </div>

    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">

        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">
                Peças da ordem de serviço
            </h2>

            {% if service_order.status != "canceled" %}
                {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                    <a href="{% url 'inventory:service_order_part_add' service_order.pk %}" class="btn btn-primary">
                        Adicionar peça
                    </a>
                {% endif %}
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Peça</th>
                        <th>Quantidade</th>
                        <th>Preço unitário</th>
                        <th>Desconto</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th class="text-end">Ações</th>
                    </tr>
                </thead>

                <tbody>
                    {% for inventory_part in inventory_parts %}
                        <tr>
                            <td>
                                {{ inventory_part.part.internal_code }} - {{ inventory_part.part.name }}
                            </td>

                            <td>
                                {{ inventory_part.quantity }}
                            </td>

                            <td>
                                {{ inventory_part.unit_price|brl }}
                            </td>

                            <td>
                                {{ inventory_part.discount|brl }}
                            </td>

                            <td>
                                {{ inventory_part.total|brl }}
                            </td>

                            <td>
                                {{ inventory_part.get_status_display }}
                            </td>

                            <td class="text-end">
                                {% if service_order.status != "canceled" %}
                                    {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                                        {% if inventory_part.status == "reserved" %}
                                            <form method="post" action="{% url 'inventory:service_order_part_confirm_usage' service_order.pk inventory_part.pk %}" class="d-inline">
                                                {% csrf_token %}
                                                <button type="submit" class="btn btn-sm btn-outline-success">
                                                    Confirmar uso
                                                </button>
                                            </form>

                                            <form method="post" action="{% url 'inventory:service_order_part_cancel' service_order.pk inventory_part.pk %}" class="d-inline">
                                                {% csrf_token %}
                                                <button type="submit" class="btn btn-sm btn-outline-danger">
                                                    Cancelar reserva
                                                </button>
                                            </form>
                                        {% elif inventory_part.status == "used" %}
                                            <form method="post" action="{% url 'inventory:service_order_part_return' service_order.pk inventory_part.pk %}" class="d-inline">
                                                {% csrf_token %}
                                                <button type="submit" class="btn btn-sm btn-outline-warning">
                                                    Devolver
                                                </button>
                                            </form>
                                        {% else %}
                                            <span class="text-muted">
                                                Sem ações
                                            </span>
                                        {% endif %}
                                    {% endif %}
                                {% else %}
                                    <span class="text-muted">
                                        OS cancelada
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="7" class="text-center text-muted py-4">
                                Nenhuma peça adicionada nesta ordem de serviço.
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>

                <tfoot>
                    <tr>
                        <th colspan="4" class="text-end">
                            Total de peças:
                        </th>
                        <th colspan="3">
                            {{ inventory_parts_total|brl }}
                        </th>
                    </tr>
                </tfoot>
            </table>
        </div>

    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">

        <h2 class="h5 mb-3">
            Itens da ordem de serviço
        </h2>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Tipo</th>
                        <th>Descrição</th>
                        <th>Quantidade</th>
                        <th>Preço unitário</th>
                        <th>Total</th>
                        <th class="text-end">Ações</th>
                    </tr>
                </thead>

                <tbody>
                    {% for item in items %}
                        <tr>
                            <td>{{ item.get_item_type_display }}</td>
                            <td>{{ item.description }}</td>
                            <td>{{ item.quantity }}</td>
                            <td>{{ item.unit_price|brl }}</td>
                            <td>{{ item.total|brl }}</td>
                            <td class="text-end">
                                {% if request.user|has_group:"Administrador" or request.user|has_group:"Atendente" %}
                                    {% if service_order.status != "canceled" %}
                                        <a href="{% url 'service_orders:service_order_item_update' service_order.pk item.pk %}" class="btn btn-sm btn-outline-secondary">
                                            Editar
                                        </a>

                                        <a href="{% url 'service_orders:service_order_item_delete' service_order.pk item.pk %}" class="btn btn-sm btn-outline-danger">
                                            Excluir
                                        </a>
                                    {% else %}
                                        <span class="text-muted">
                                            Ordem cancelada
                                        </span>
                                    {% endif %}
                                {% else %}
                                    <span class="text-muted">
                                        Somente visualização
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-4">
                                Nenhum item cadastrado nesta ordem de serviço.
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>

                <tfoot>
                    <tr>
                        <th colspan="4" class="text-end">
                            Subtotal dos itens:
                        </th>
                        <th colspan="2">
                            {{ service_order.items_total|brl }}
                        </th>
                    </tr>
                </tfoot>
            </table>
        </div>

    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">

        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">
                Controle de tempo
            </h2>

            {% if request.user|has_group:"Administrador" or request.user|has_group:"Mecânico" %}
                {% if service_order.status != "canceled" %}
                    {% if open_time_entry %}
                        <span class="badge text-bg-warning">
                            Tempo em andamento
                        </span>
                    {% else %}
                        <form method="post" action="{% url 'service_orders:service_order_time_start' service_order.pk %}">
                            {% csrf_token %}

                            <button type="submit" class="btn btn-sm btn-success">
                                Iniciar tempo
                            </button>
                        </form>
                    {% endif %}
                {% endif %}
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
                <thead>
                    <tr>
                        <th>Mecânico</th>
                        <th>Início</th>
                        <th>Fim</th>
                        <th>Duração</th>
                        <th>Observação</th>
                        <th class="text-end">Ações</th>
                    </tr>
                </thead>

                <tbody>
                    {% for entry in time_entries %}
                        <tr>
                            <td>{{ entry.mechanic.email }}</td>
                            <td>{{ entry.started_at|date:"d/m/Y H:i" }}</td>
                            <td>{{ entry.ended_at|date:"d/m/Y H:i"|default:"Em andamento" }}</td>
                            <td>{{ entry.duration }}</td>
                            <td>{{ entry.note|default:"-" }}</td>
                            <td class="text-end">
                                {% if entry.is_open %}
                                    {% if request.user == entry.mechanic or request.user|has_group:"Administrador" %}
                                        <form method="post" action="{% url 'service_orders:service_order_time_finish' service_order.pk entry.pk %}">
                                            {% csrf_token %}

                                            <textarea
                                                name="note"
                                                class="form-control form-control-sm mb-2"
                                                placeholder="Observação do apontamento"
                                                rows="2"
                                            ></textarea>

                                            <button type="submit" class="btn btn-sm btn-outline-danger">
                                                Encerrar
                                            </button>
                                        </form>
                                    {% else %}
                                        <span class="text-muted">
                                            Em andamento
                                        </span>
                                    {% endif %}
                                {% else %}
                                    <span class="text-muted">
                                        Encerrado
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-3">
                                Nenhum apontamento de tempo registrado.
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">

        <h2 class="h5 mb-3">
            Histórico de alterações
        </h2>

        <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Usuário</th>
                        <th>Campo</th>
                        <th>Valor antigo</th>
                        <th>Valor novo</th>
                    </tr>
                </thead>

                <tbody>
                    {% for history in histories %}
                        <tr>
                            <td>{{ history.created_at|date:"d/m/Y H:i" }}</td>
                            <td>{{ history.changed_by.email }}</td>
                            <td>{{ history.field_name }}</td>
                            <td>{{ history.old_value|default:"-" }}</td>
                            <td>{{ history.new_value|default:"-" }}</td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-3">
                                Nenhuma alteração registrada até o momento.
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

    </div>
</div>

<div class="d-flex justify-content-between">
    <a href="{% url 'service_orders:service_order_list' %}" class="btn btn-outline-secondary">
        Voltar
    </a>

    {% if request.user|has_group:"Administrador" %}
        {% if service_order.status != "canceled" %}
            <a href="{% url 'service_orders:service_order_cancel' service_order.pk %}" class="btn btn-outline-warning">
                Cancelar ordem de serviço
            </a>
        {% endif %}
    {% endif %}
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">CRM vinculado à OS</h2>
            <div class="d-flex gap-2">
                <a href="{% url 'crm:interaction_create' %}?customer={{ service_order.customer.pk }}&service_order={{ service_order.pk }}" class="btn btn-sm btn-outline-primary">Registrar interação</a>
                <a href="{% url 'crm:opportunity_create' %}?customer={{ service_order.customer.pk }}&vehicle={{ service_order.vehicle.pk }}&service_order={{ service_order.pk }}" class="btn btn-sm btn-outline-secondary">Criar oportunidade</a>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-sm table-hover align-middle mb-0">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Canal</th>
                        <th>Assunto</th>
                        <th>Responsável</th>
                    </tr>
                </thead>
                <tbody>
                    {% for interaction in crm_timeline %}
                        <tr>
                            <td>{{ interaction.interaction_date|date:"d/m/Y H:i" }}</td>
                            <td>{{ interaction.get_interaction_type_display }}</td>
                            <td>{{ interaction.get_channel_display }}</td>
                            <td>{{ interaction.subject }}</td>
                            <td>{{ interaction.responsible_user|default:"Sistema" }}</td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-3">Nenhuma interação de CRM vinculada a esta OS.</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

{% endblock %}
'@ | Set-Content -Encoding UTF8 "templates/service_orders/service_order_detail.html"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'

'@ | Set-Content -Encoding UTF8 "crm/__init__.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django.contrib import admin

from .models import Campaign, CampaignAudience, CustomerInteraction, CustomerOpportunity, CustomerReminder, CustomerTag


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    search_fields = ["name"]


@admin.register(CustomerInteraction)
class CustomerInteractionAdmin(admin.ModelAdmin):
    list_display = ["customer", "interaction_type", "channel", "subject", "responsible_user", "interaction_date"]
    list_filter = ["interaction_type", "channel", "interaction_date"]
    search_fields = ["customer__name", "subject", "description"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


@admin.register(CustomerOpportunity)
class CustomerOpportunityAdmin(admin.ModelAdmin):
    list_display = ["title", "customer", "status", "estimated_value", "probability", "expected_close_date"]
    list_filter = ["status", "expected_close_date"]
    search_fields = ["title", "customer__name"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


@admin.register(CustomerReminder)
class CustomerReminderAdmin(admin.ModelAdmin):
    list_display = ["title", "customer", "due_date", "status", "responsible_user"]
    list_filter = ["status", "due_date"]
    search_fields = ["title", "customer__name"]
    autocomplete_fields = ["customer", "vehicle", "service_order", "responsible_user"]


class CampaignAudienceInline(admin.TabularInline):
    model = CampaignAudience
    extra = 0
    autocomplete_fields = ["customer"]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "campaign_type", "channel", "status", "scheduled_at", "created_by"]
    list_filter = ["campaign_type", "channel", "status"]
    search_fields = ["name", "subject", "message"]
    inlines = [CampaignAudienceInline]

'@ | Set-Content -Encoding UTF8 "crm/admin.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crm"
    verbose_name = "CRM"

'@ | Set-Content -Encoding UTF8 "crm/apps.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django import forms

from .models import Campaign, CampaignAudience, CustomerInteraction, CustomerOpportunity, CustomerReminder


class CustomerInteractionForm(forms.ModelForm):
    class Meta:
        model = CustomerInteraction
        fields = ["customer", "vehicle", "service_order", "interaction_type", "channel", "subject", "description", "next_follow_up_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }


class CustomerOpportunityForm(forms.ModelForm):
    class Meta:
        model = CustomerOpportunity
        fields = ["customer", "vehicle", "service_order", "title", "description", "estimated_value", "probability", "status", "expected_close_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "expected_close_date": forms.DateInput(attrs={"type": "date"}),
        }


class CustomerReminderForm(forms.ModelForm):
    class Meta:
        model = CustomerReminder
        fields = ["customer", "vehicle", "service_order", "title", "notes", "due_date", "status"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "campaign_type", "channel", "subject", "message", "status", "scheduled_at"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class CampaignAudienceForm(forms.ModelForm):
    class Meta:
        model = CampaignAudience
        fields = ["customer"]

'@ | Set-Content -Encoding UTF8 "crm/forms.py"

New-Item -ItemType Directory -Force -Path "crm/migrations" | Out-Null

@'
# Generated manually for MotorMind CRM on 2026-05-04

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("service_orders", "0006_serviceordertimeentry"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nome")),
                ("campaign_type", models.CharField(choices=[("post_sale", "Pós-venda"), ("preventive_maintenance", "Revisão preventiva"), ("inactive_customers", "Clientes inativos"), ("promotion", "Promoção"), ("birthday", "Aniversário")], max_length=40, verbose_name="Tipo")),
                ("channel", models.CharField(choices=[("email", "E-mail"), ("whatsapp", "WhatsApp"), ("phone", "Telefone")], max_length=20, verbose_name="Canal")),
                ("subject", models.CharField(max_length=150, verbose_name="Assunto")),
                ("message", models.TextField(verbose_name="Mensagem")),
                ("status", models.CharField(choices=[("draft", "Rascunho"), ("scheduled", "Agendada"), ("running", "Em execução"), ("finished", "Finalizada"), ("canceled", "Cancelada")], default="draft", max_length=20, verbose_name="Status")),
                ("scheduled_at", models.DateTimeField(blank=True, null=True, verbose_name="Agendada para")),
                ("started_at", models.DateTimeField(blank=True, null=True, verbose_name="Iniciada em")),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="Finalizada em")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_campaigns", to=settings.AUTH_USER_MODEL, verbose_name="Criada por")),
            ],
            options={"verbose_name": "Campanha de CRM", "verbose_name_plural": "Campanhas de CRM", "ordering": ["status", "-created_at"]},
        ),
        migrations.CreateModel(
            name="CustomerTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="Nome")),
                ("color", models.CharField(blank=True, max_length=20, verbose_name="Cor CSS")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
            ],
            options={"verbose_name": "Tag de cliente", "verbose_name_plural": "Tags de cliente", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CustomerInteraction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interaction_type", models.CharField(choices=[("call", "Ligação"), ("whatsapp", "WhatsApp"), ("email", "E-mail"), ("visit", "Visita"), ("service_order", "Ordem de serviço"), ("post_sale", "Pós-venda"), ("portal", "Portal do cliente"), ("campaign", "Campanha"), ("internal", "Interna")], max_length=30, verbose_name="Tipo")),
                ("channel", models.CharField(choices=[("phone", "Telefone"), ("whatsapp", "WhatsApp"), ("email", "E-mail"), ("in_person", "Presencial"), ("system", "Sistema"), ("portal", "Portal"), ("other", "Outro")], default="system", max_length=30, verbose_name="Canal")),
                ("subject", models.CharField(max_length=150, verbose_name="Assunto")),
                ("description", models.TextField(verbose_name="Descrição")),
                ("interaction_date", models.DateTimeField(verbose_name="Data da interação")),
                ("next_follow_up_date", models.DateField(blank=True, null=True, verbose_name="Próximo follow-up")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_interactions", to="customers.customer", verbose_name="Cliente")),
                ("responsible_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_interactions", to=settings.AUTH_USER_MODEL, verbose_name="Responsável")),
                ("service_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_interactions", to="service_orders.serviceorder", verbose_name="Ordem de serviço")),
                ("vehicle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_interactions", to="customers.vehicle", verbose_name="Veículo")),
            ],
            options={"verbose_name": "Interação de CRM", "verbose_name_plural": "Interações de CRM", "ordering": ["-interaction_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="CustomerOpportunity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150, verbose_name="Título")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                ("estimated_value", models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Valor estimado")),
                ("probability", models.PositiveSmallIntegerField(default=50, verbose_name="Probabilidade (%)")),
                ("status", models.CharField(choices=[("open", "Aberta"), ("won", "Ganha"), ("lost", "Perdida"), ("canceled", "Cancelada")], default="open", max_length=20, verbose_name="Status")),
                ("expected_close_date", models.DateField(blank=True, null=True, verbose_name="Previsão de fechamento")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_opportunities", to="customers.customer", verbose_name="Cliente")),
                ("responsible_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_opportunities", to=settings.AUTH_USER_MODEL, verbose_name="Responsável")),
                ("service_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_opportunities", to="service_orders.serviceorder", verbose_name="Ordem de serviço")),
                ("vehicle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_opportunities", to="customers.vehicle", verbose_name="Veículo")),
            ],
            options={"verbose_name": "Oportunidade de CRM", "verbose_name_plural": "Oportunidades de CRM", "ordering": ["status", "expected_close_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="CustomerReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150, verbose_name="Título")),
                ("notes", models.TextField(blank=True, verbose_name="Observações")),
                ("due_date", models.DateField(verbose_name="Data de vencimento")),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("done", "Concluído"), ("canceled", "Cancelado")], default="pending", max_length=20, verbose_name="Status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_reminders", to="customers.customer", verbose_name="Cliente")),
                ("responsible_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_reminders", to=settings.AUTH_USER_MODEL, verbose_name="Responsável")),
                ("service_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_reminders", to="service_orders.serviceorder", verbose_name="Ordem de serviço")),
                ("vehicle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_reminders", to="customers.vehicle", verbose_name="Veículo")),
            ],
            options={"verbose_name": "Lembrete de CRM", "verbose_name_plural": "Lembretes de CRM", "ordering": ["status", "due_date", "customer__name"]},
        ),
        migrations.CreateModel(
            name="CampaignAudience",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audience", to="crm.campaign", verbose_name="Campanha")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_campaign_audiences", to="customers.customer", verbose_name="Cliente")),
            ],
            options={"verbose_name": "Público da campanha", "verbose_name_plural": "Público das campanhas", "unique_together": {("campaign", "customer")}},
        ),
        migrations.AddIndex(model_name="customerinteraction", index=models.Index(fields=["customer", "-interaction_date"], name="crm_custome_custome_74f7ca_idx")),
        migrations.AddIndex(model_name="customerinteraction", index=models.Index(fields=["service_order", "-interaction_date"], name="crm_custome_service_0a6c95_idx")),
        migrations.AddIndex(model_name="customerinteraction", index=models.Index(fields=["next_follow_up_date"], name="crm_custome_next_fo_2d885e_idx")),
        migrations.AddIndex(model_name="customerreminder", index=models.Index(fields=["status", "due_date"], name="crm_custome_status_dcfbd4_idx")),
    ]

'@ | Set-Content -Encoding UTF8 "crm/migrations/0001_initial.py"

New-Item -ItemType Directory -Force -Path "crm/migrations" | Out-Null

@'

'@ | Set-Content -Encoding UTF8 "crm/migrations/__init__.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


class CustomerTag(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name="Nome")
    color = models.CharField(max_length=20, blank=True, verbose_name="Cor CSS")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Tag de cliente"
        verbose_name_plural = "Tags de cliente"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerInteraction(models.Model):
    class InteractionType(models.TextChoices):
        CALL = "call", "Ligação"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        VISIT = "visit", "Visita"
        SERVICE_ORDER = "service_order", "Ordem de serviço"
        POST_SALE = "post_sale", "Pós-venda"
        PORTAL = "portal", "Portal do cliente"
        CAMPAIGN = "campaign", "Campanha"
        INTERNAL = "internal", "Interna"

    class Channel(models.TextChoices):
        PHONE = "phone", "Telefone"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        IN_PERSON = "in_person", "Presencial"
        SYSTEM = "system", "Sistema"
        PORTAL = "portal", "Portal"
        OTHER = "other", "Outro"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="crm_interactions", verbose_name="Cliente")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name="crm_interactions", blank=True, null=True, verbose_name="Veículo")
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.SET_NULL, related_name="crm_interactions", blank=True, null=True, verbose_name="Ordem de serviço")
    interaction_type = models.CharField(max_length=30, choices=InteractionType.choices, verbose_name="Tipo")
    channel = models.CharField(max_length=30, choices=Channel.choices, default=Channel.SYSTEM, verbose_name="Canal")
    subject = models.CharField(max_length=150, verbose_name="Assunto")
    description = models.TextField(verbose_name="Descrição")
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="crm_interactions", blank=True, null=True, verbose_name="Responsável")
    interaction_date = models.DateTimeField(default=timezone.now, verbose_name="Data da interação")
    next_follow_up_date = models.DateField(blank=True, null=True, verbose_name="Próximo follow-up")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Interação de CRM"
        verbose_name_plural = "Interações de CRM"
        ordering = ["-interaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["customer", "-interaction_date"]),
            models.Index(fields=["service_order", "-interaction_date"]),
            models.Index(fields=["next_follow_up_date"]),
        ]

    def __str__(self):
        return f"{self.customer} - {self.subject}"


class CustomerOpportunity(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Aberta"
        WON = "won", "Ganha"
        LOST = "lost", "Perdida"
        CANCELED = "canceled", "Cancelada"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="crm_opportunities", verbose_name="Cliente")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name="crm_opportunities", blank=True, null=True, verbose_name="Veículo")
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.SET_NULL, related_name="crm_opportunities", blank=True, null=True, verbose_name="Ordem de serviço")
    title = models.CharField(max_length=150, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Valor estimado")
    probability = models.PositiveSmallIntegerField(default=50, verbose_name="Probabilidade (%)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, verbose_name="Status")
    expected_close_date = models.DateField(blank=True, null=True, verbose_name="Previsão de fechamento")
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="crm_opportunities", blank=True, null=True, verbose_name="Responsável")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Oportunidade de CRM"
        verbose_name_plural = "Oportunidades de CRM"
        ordering = ["status", "expected_close_date", "-created_at"]

    def __str__(self):
        return self.title


class CustomerReminder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        DONE = "done", "Concluído"
        CANCELED = "canceled", "Cancelado"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="crm_reminders", verbose_name="Cliente")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name="crm_reminders", blank=True, null=True, verbose_name="Veículo")
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.SET_NULL, related_name="crm_reminders", blank=True, null=True, verbose_name="Ordem de serviço")
    title = models.CharField(max_length=150, verbose_name="Título")
    notes = models.TextField(blank=True, verbose_name="Observações")
    due_date = models.DateField(verbose_name="Data de vencimento")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Status")
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="crm_reminders", blank=True, null=True, verbose_name="Responsável")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Lembrete de CRM"
        verbose_name_plural = "Lembretes de CRM"
        ordering = ["status", "due_date", "customer__name"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return self.title


class Campaign(models.Model):
    class CampaignType(models.TextChoices):
        POST_SALE = "post_sale", "Pós-venda"
        PREVENTIVE_MAINTENANCE = "preventive_maintenance", "Revisão preventiva"
        INACTIVE_CUSTOMERS = "inactive_customers", "Clientes inativos"
        PROMOTION = "promotion", "Promoção"
        BIRTHDAY = "birthday", "Aniversário"

    class Channel(models.TextChoices):
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        PHONE = "phone", "Telefone"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SCHEDULED = "scheduled", "Agendada"
        RUNNING = "running", "Em execução"
        FINISHED = "finished", "Finalizada"
        CANCELED = "canceled", "Cancelada"

    name = models.CharField(max_length=150, verbose_name="Nome")
    campaign_type = models.CharField(max_length=40, choices=CampaignType.choices, verbose_name="Tipo")
    channel = models.CharField(max_length=20, choices=Channel.choices, verbose_name="Canal")
    subject = models.CharField(max_length=150, verbose_name="Assunto")
    message = models.TextField(verbose_name="Mensagem")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Status")
    scheduled_at = models.DateTimeField(blank=True, null=True, verbose_name="Agendada para")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="Iniciada em")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="Finalizada em")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="crm_campaigns", blank=True, null=True, verbose_name="Criada por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Campanha de CRM"
        verbose_name_plural = "Campanhas de CRM"
        ordering = ["status", "-created_at"]

    def __str__(self):
        return self.name


class CampaignAudience(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="audience", verbose_name="Campanha")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="crm_campaign_audiences", verbose_name="Cliente")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Público da campanha"
        verbose_name_plural = "Público das campanhas"
        unique_together = ["campaign", "customer"]

    def __str__(self):
        return f"{self.campaign} - {self.customer}"

'@ | Set-Content -Encoding UTF8 "crm/models.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from core.permissions import ADMIN_GROUP, ATTENDANT_GROUP, FINANCIAL_GROUP, user_in_any_group, user_in_group


def can_view_crm(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP, FINANCIAL_GROUP])


def can_manage_crm(user):
    return user_in_any_group(user, [ADMIN_GROUP, ATTENDANT_GROUP])


def can_manage_crm_campaigns(user):
    return user_in_group(user, ADMIN_GROUP)

'@ | Set-Content -Encoding UTF8 "crm/permissions.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone

from customers.models import Customer
from service_orders.models import ServiceOrder

from .models import Campaign, CustomerInteraction, CustomerOpportunity, CustomerReminder


def get_crm_dashboard_data():
    today = timezone.localdate()
    inactive_limit = today - timedelta(days=180)

    customers_with_last_order = Customer.objects.annotate(
        last_order_at=Max("service_orders__created_at"),
        open_opportunities_count=Count(
            "crm_opportunities",
            filter=Q(crm_opportunities__status=CustomerOpportunity.Status.OPEN),
        ),
    )

    inactive_customers = customers_with_last_order.filter(
        Q(last_order_at__date__lt=inactive_limit) | Q(last_order_at__isnull=True),
        is_active=True,
    )

    return {
        "total_customers": Customer.objects.filter(is_active=True).count(),
        "interactions_today": CustomerInteraction.objects.filter(interaction_date__date=today).count(),
        "pending_reminders": CustomerReminder.objects.filter(status=CustomerReminder.Status.PENDING, due_date__lte=today).count(),
        "open_opportunities": CustomerOpportunity.objects.filter(status=CustomerOpportunity.Status.OPEN).count(),
        "active_campaigns": Campaign.objects.filter(status__in=[Campaign.Status.SCHEDULED, Campaign.Status.RUNNING]).count(),
        "inactive_customers_count": inactive_customers.count(),
        "latest_interactions": CustomerInteraction.objects.select_related("customer", "vehicle", "service_order", "responsible_user")[:10],
        "due_reminders": CustomerReminder.objects.select_related("customer", "vehicle", "service_order", "responsible_user").filter(status=CustomerReminder.Status.PENDING, due_date__lte=today)[:10],
        "inactive_customers": inactive_customers.order_by("last_order_at", "name")[:10],
    }


def get_customer_crm_summary(customer):
    return {
        "interactions": customer.crm_interactions.select_related("vehicle", "service_order", "responsible_user")[:10],
        "open_opportunities": customer.crm_opportunities.filter(status=CustomerOpportunity.Status.OPEN).select_related("vehicle", "service_order", "responsible_user"),
        "pending_reminders": customer.crm_reminders.filter(status=CustomerReminder.Status.PENDING).select_related("vehicle", "service_order", "responsible_user"),
    }


def get_service_order_crm_timeline(service_order):
    return service_order.crm_interactions.select_related("customer", "vehicle", "responsible_user").all()


def get_inactive_customers(days=180):
    limit = timezone.localdate() - timedelta(days=days)
    return Customer.objects.annotate(last_order_at=Max("service_orders__created_at")).filter(
        Q(last_order_at__date__lt=limit) | Q(last_order_at__isnull=True),
        is_active=True,
    ).order_by("last_order_at", "name")


def get_post_sale_candidates(days_after_finished=3):
    target_date = timezone.localdate() - timedelta(days=days_after_finished)
    return ServiceOrder.objects.select_related("customer", "vehicle").filter(
        status=ServiceOrder.Status.FINISHED,
        finished_at__date__lte=target_date,
    ).exclude(
        crm_interactions__interaction_type=CustomerInteraction.InteractionType.POST_SALE,
    )

'@ | Set-Content -Encoding UTF8 "crm/selectors.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from auditoria.models import AuditLog
from auditoria.services import log_event, serialize_instance
from service_orders.models import ServiceOrder

from .models import CustomerInteraction, CustomerOpportunity, CustomerReminder


@transaction.atomic
def create_interaction(*, customer, subject, description, responsible_user=None, interaction_type=CustomerInteraction.InteractionType.INTERNAL, channel=CustomerInteraction.Channel.SYSTEM, vehicle=None, service_order=None, next_follow_up_date=None):
    interaction = CustomerInteraction.objects.create(
        customer=customer,
        vehicle=vehicle,
        service_order=service_order,
        interaction_type=interaction_type,
        channel=channel,
        subject=subject,
        description=description,
        responsible_user=responsible_user,
        next_follow_up_date=next_follow_up_date,
    )
    log_event(action=AuditLog.Action.CREATE, user=responsible_user, obj=interaction, new_data=serialize_instance(interaction))
    return interaction


@transaction.atomic
def create_opportunity_from_service_order(*, service_order, title, description="", estimated_value=0, responsible_user=None, expected_close_date=None):
    opportunity = CustomerOpportunity.objects.create(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        title=title,
        description=description,
        estimated_value=estimated_value,
        responsible_user=responsible_user,
        expected_close_date=expected_close_date,
    )
    create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=responsible_user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="Oportunidade criada a partir da OS",
        description=f"Oportunidade registrada: {title}",
    )
    log_event(action=AuditLog.Action.CREATE, user=responsible_user, obj=opportunity, new_data=serialize_instance(opportunity))
    return opportunity


@transaction.atomic
def create_reminder(*, customer, title, due_date, notes="", responsible_user=None, vehicle=None, service_order=None):
    reminder = CustomerReminder.objects.create(
        customer=customer,
        vehicle=vehicle,
        service_order=service_order,
        title=title,
        notes=notes,
        due_date=due_date,
        responsible_user=responsible_user,
    )
    log_event(action=AuditLog.Action.CREATE, user=responsible_user, obj=reminder, new_data=serialize_instance(reminder))
    return reminder


@transaction.atomic
def mark_reminder_done(reminder, user):
    old_data = serialize_instance(reminder)
    reminder.status = CustomerReminder.Status.DONE
    reminder.save(update_fields=["status", "updated_at"])
    log_event(action=AuditLog.Action.UPDATE, user=user, obj=reminder, old_data=old_data, new_data=serialize_instance(reminder))
    return reminder


def register_service_order_opened(service_order, user):
    return create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="OS aberta",
        description=f"Ordem de serviço #{service_order.pk} aberta: {service_order.title}",
    )


def register_service_order_status_change(service_order, user, old_status, new_status):
    interaction = create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="Status da OS alterado",
        description=f"OS #{service_order.pk}: status alterado de {old_status} para {new_status}.",
    )

    if new_status == ServiceOrder.Status.FINISHED:
        create_reminder(
            customer=service_order.customer,
            vehicle=service_order.vehicle,
            service_order=service_order,
            responsible_user=user,
            title=f"Pós-venda da OS #{service_order.pk}",
            notes="Entrar em contato para confirmar satisfação, dúvidas e possível revisão preventiva.",
            due_date=timezone.localdate() + timedelta(days=3),
        )
    return interaction


def register_service_order_canceled(service_order, user):
    return create_interaction(
        customer=service_order.customer,
        vehicle=service_order.vehicle,
        service_order=service_order,
        responsible_user=user,
        interaction_type=CustomerInteraction.InteractionType.SERVICE_ORDER,
        channel=CustomerInteraction.Channel.SYSTEM,
        subject="OS cancelada",
        description=f"Ordem de serviço #{service_order.pk} cancelada.",
    )

'@ | Set-Content -Encoding UTF8 "crm/services.py"

New-Item -ItemType Directory -Force -Path "crm/tests" | Out-Null

@'

'@ | Set-Content -Encoding UTF8 "crm/tests/__init__.py"

New-Item -ItemType Directory -Force -Path "crm/tests" | Out-Null

@'
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from crm.models import CustomerInteraction, CustomerReminder
from crm.services import register_service_order_opened, register_service_order_status_change
from customers.models import Customer, Vehicle
from service_orders.models import ServiceOrder


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(email="admin@example.com", password="test123456")


@pytest.fixture
def customer(db):
    return Customer.objects.create(name="Cliente CRM", phone="11999999999", email="cliente@example.com")


@pytest.fixture
def vehicle(customer):
    return Vehicle.objects.create(customer=customer, plate="CRM1234", brand="Fiat", model="Uno")


@pytest.fixture
def service_order(customer, vehicle, user):
    return ServiceOrder.objects.create(
        customer=customer,
        vehicle=vehicle,
        created_by=user,
        title="Revisão",
        description="Revisão preventiva",
    )


@pytest.mark.django_db
def test_register_service_order_opened_creates_crm_interaction(service_order, user):
    interaction = register_service_order_opened(service_order, user)

    assert interaction.customer == service_order.customer
    assert interaction.service_order == service_order
    assert interaction.interaction_type == CustomerInteraction.InteractionType.SERVICE_ORDER


@pytest.mark.django_db
def test_finished_status_creates_post_sale_reminder(service_order, user):
    register_service_order_status_change(
        service_order,
        user,
        ServiceOrder.Status.IN_PROGRESS,
        ServiceOrder.Status.FINISHED,
    )

    reminder = CustomerReminder.objects.get(service_order=service_order)
    assert reminder.status == CustomerReminder.Status.PENDING
    assert reminder.due_date == timezone.localdate() + timedelta(days=3)

'@ | Set-Content -Encoding UTF8 "crm/tests/test_services.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("", views.crm_dashboard_view, name="dashboard"),
    path("interacoes/", views.interaction_list_view, name="interaction_list"),
    path("interacoes/nova/", views.interaction_create_view, name="interaction_create"),
    path("oportunidades/", views.opportunity_list_view, name="opportunity_list"),
    path("oportunidades/nova/", views.opportunity_create_view, name="opportunity_create"),
    path("lembretes/", views.reminder_list_view, name="reminder_list"),
    path("lembretes/novo/", views.reminder_create_view, name="reminder_create"),
    path("lembretes/<int:pk>/concluir/", views.reminder_done_view, name="reminder_done"),
    path("clientes-inativos/", views.inactive_customer_list_view, name="inactive_customer_list"),
    path("campanhas/", views.campaign_list_view, name="campaign_list"),
    path("campanhas/nova/", views.campaign_create_view, name="campaign_create"),
    path("campanhas/<int:pk>/publico/adicionar/", views.campaign_audience_add_view, name="campaign_audience_add"),
]

'@ | Set-Content -Encoding UTF8 "crm/urls.py"

New-Item -ItemType Directory -Force -Path "crm" | Out-Null

@'
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import user_passes_permission

from .forms import CampaignAudienceForm, CampaignForm, CustomerInteractionForm, CustomerOpportunityForm, CustomerReminderForm
from .models import Campaign, CampaignAudience, CustomerInteraction, CustomerOpportunity, CustomerReminder
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
    interactions = CustomerInteraction.objects.select_related("customer", "vehicle", "service_order", "responsible_user")
    if search:
        interactions = interactions.filter(Q(customer__name__icontains=search) | Q(subject__icontains=search) | Q(description__icontains=search))
    return render(request, "crm/interaction_list.html", {"interactions": interactions, "search": search})


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
        messages.error(request, "Não foi possível registrar a interação. Verifique os dados.")
    else:
        form = CustomerInteractionForm(initial=initial)
    return render(request, "crm/form.html", {"form": form, "page_title": "Registrar interação", "button_text": "Salvar interação"})


@login_required
@user_passes_permission(can_view_crm)
def opportunity_list_view(request):
    opportunities = CustomerOpportunity.objects.select_related("customer", "vehicle", "service_order", "responsible_user")
    status = request.GET.get("status", "")
    if status:
        opportunities = opportunities.filter(status=status)
    return render(request, "crm/opportunity_list.html", {"opportunities": opportunities, "status": status, "status_choices": CustomerOpportunity.Status.choices})


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
    return render(request, "crm/form.html", {"form": form, "page_title": "Cadastrar oportunidade", "button_text": "Salvar oportunidade"})


@login_required
@user_passes_permission(can_view_crm)
def reminder_list_view(request):
    reminders = CustomerReminder.objects.select_related("customer", "vehicle", "service_order", "responsible_user")
    status = request.GET.get("status", CustomerReminder.Status.PENDING)
    if status:
        reminders = reminders.filter(status=status)
    return render(request, "crm/reminder_list.html", {"reminders": reminders, "status": status, "status_choices": CustomerReminder.Status.choices})


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
    return render(request, "crm/form.html", {"form": form, "page_title": "Cadastrar lembrete", "button_text": "Salvar lembrete"})


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
    return render(request, "crm/inactive_customer_list.html", {"customers": customers, "days": days})


@login_required
@user_passes_permission(can_view_crm)
def campaign_list_view(request):
    campaigns = Campaign.objects.select_related("created_by").prefetch_related("audience")
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
    return render(request, "crm/form.html", {"form": form, "page_title": "Criar campanha", "button_text": "Salvar campanha"})


@login_required
@user_passes_permission(can_manage_crm_campaigns)
def campaign_audience_add_view(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == "POST":
        form = CampaignAudienceForm(request.POST)
        if form.is_valid():
            CampaignAudience.objects.get_or_create(campaign=campaign, customer=form.cleaned_data["customer"])
            messages.success(request, "Cliente adicionado ao público da campanha.")
            return redirect("crm:campaign_list")
    else:
        form = CampaignAudienceForm()
    return render(request, "crm/form.html", {"form": form, "page_title": f"Adicionar público - {campaign.name}", "button_text": "Adicionar cliente"})

'@ | Set-Content -Encoding UTF8 "crm/views.py"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% block title %}Campanhas - CRM{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4"><div><h1 class="h4 mb-1">Campanhas</h1><p class="text-muted mb-0">Campanhas comerciais, pós-venda e revisão preventiva.</p></div><a href="{% url 'crm:campaign_create' %}" class="btn btn-primary">Nova campanha</a></div>
<div class="card shadow-sm"><div class="card-body"><div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th>Nome</th><th>Tipo</th><th>Canal</th><th>Status</th><th>Público</th><th>Agendamento</th><th class="text-end">Ações</th></tr></thead><tbody>{% for campaign in campaigns %}<tr><td>{{ campaign.name }}</td><td>{{ campaign.get_campaign_type_display }}</td><td>{{ campaign.get_channel_display }}</td><td>{{ campaign.get_status_display }}</td><td>{{ campaign.audience.count }}</td><td>{{ campaign.scheduled_at|date:"d/m/Y H:i"|default:"-" }}</td><td class="text-end"><a href="{% url 'crm:campaign_audience_add' campaign.pk %}" class="btn btn-sm btn-outline-primary">Adicionar público</a></td></tr>{% empty %}<tr><td colspan="7" class="text-center text-muted py-4">Nenhuma campanha cadastrada.</td></tr>{% endfor %}</tbody></table></div></div></div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/campaign_list.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% load group_tags %}

{% block title %}CRM - MotorMind{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h4 mb-1">CRM</h1>
        <p class="text-muted mb-0">Relacionamento, oportunidades, follow-ups, campanhas e clientes inativos.</p>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'crm:interaction_create' %}" class="btn btn-primary">Nova interação</a>
        <a href="{% url 'crm:reminder_create' %}" class="btn btn-outline-primary">Novo lembrete</a>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Clientes ativos</span><h2 class="h4 mb-0">{{ total_customers }}</h2></div></div></div>
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Interações hoje</span><h2 class="h4 mb-0">{{ interactions_today }}</h2></div></div></div>
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Follow-ups vencidos</span><h2 class="h4 mb-0">{{ pending_reminders }}</h2></div></div></div>
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Oportunidades</span><h2 class="h4 mb-0">{{ open_opportunities }}</h2></div></div></div>
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Campanhas ativas</span><h2 class="h4 mb-0">{{ active_campaigns }}</h2></div></div></div>
    <div class="col-md-2"><div class="card shadow-sm"><div class="card-body"><span class="text-muted small">Clientes inativos</span><h2 class="h4 mb-0">{{ inactive_customers_count }}</h2></div></div></div>
</div>

<div class="row g-3 mb-4">
    <div class="col-lg-8">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2 class="h5 mb-0">Últimas interações</h2>
                    <a href="{% url 'crm:interaction_list' %}" class="btn btn-sm btn-outline-secondary">Ver todas</a>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead><tr><th>Data</th><th>Cliente</th><th>Tipo</th><th>Assunto</th><th>Responsável</th></tr></thead>
                        <tbody>
                            {% for interaction in latest_interactions %}
                                <tr>
                                    <td>{{ interaction.interaction_date|date:"d/m/Y H:i" }}</td>
                                    <td><a href="{% url 'customers:customer_detail' interaction.customer.pk %}">{{ interaction.customer.name }}</a></td>
                                    <td>{{ interaction.get_interaction_type_display }}</td>
                                    <td>{{ interaction.subject }}</td>
                                    <td>{{ interaction.responsible_user|default:"Sistema" }}</td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="5" class="text-center text-muted py-4">Nenhuma interação registrada.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2 class="h5 mb-0">Follow-ups pendentes</h2>
                    <a href="{% url 'crm:reminder_list' %}" class="btn btn-sm btn-outline-secondary">Ver todos</a>
                </div>
                {% for reminder in due_reminders %}
                    <div class="border-bottom pb-2 mb-2">
                        <strong>{{ reminder.title }}</strong><br>
                        <span class="text-muted small">{{ reminder.customer.name }} · {{ reminder.due_date|date:"d/m/Y" }}</span>
                    </div>
                {% empty %}
                    <p class="text-muted mb-0">Nenhum follow-up vencido.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<div class="card shadow-sm">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">Clientes inativos</h2>
            <a href="{% url 'crm:inactive_customer_list' %}" class="btn btn-sm btn-outline-secondary">Analisar lista</a>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead><tr><th>Cliente</th><th>Telefone</th><th>Email</th><th>Última OS</th><th class="text-end">Ação</th></tr></thead>
                <tbody>
                    {% for customer in inactive_customers %}
                        <tr>
                            <td>{{ customer.name }}</td>
                            <td>{{ customer.phone }}</td>
                            <td>{{ customer.email|default:"-" }}</td>
                            <td>{{ customer.last_order_at|date:"d/m/Y"|default:"Sem OS" }}</td>
                            <td class="text-end"><a href="{% url 'crm:interaction_create' %}?customer={{ customer.pk }}" class="btn btn-sm btn-outline-primary">Registrar contato</a></td>
                        </tr>
                    {% empty %}
                        <tr><td colspan="5" class="text-center text-muted py-4">Nenhum cliente inativo encontrado.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/dashboard.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block title %}{{ page_title }} - CRM{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card shadow-sm">
            <div class="card-body">
                <h1 class="h4 mb-4">{{ page_title }}</h1>
                <form method="post" novalidate>
                    {% csrf_token %}
                    {{ form|crispy }}
                    <div class="d-flex gap-2 mt-3">
                        <button type="submit" class="btn btn-primary">{{ button_text }}</button>
                        <a href="{% url 'crm:dashboard' %}" class="btn btn-outline-secondary">Cancelar</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/form.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% block title %}Clientes inativos - CRM{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4"><div><h1 class="h4 mb-1">Clientes inativos</h1><p class="text-muted mb-0">Clientes sem OS nos últimos {{ days }} dias ou sem OS registrada.</p></div><a href="{% url 'crm:dashboard' %}" class="btn btn-outline-secondary">Voltar ao CRM</a></div>
<form method="get" class="card card-body shadow-sm mb-3"><div class="input-group"><span class="input-group-text">Dias sem OS</span><input type="number" name="days" value="{{ days }}" min="30" class="form-control"><button class="btn btn-outline-secondary" type="submit">Filtrar</button></div></form>
<div class="card shadow-sm"><div class="card-body"><div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th>Cliente</th><th>Telefone</th><th>Email</th><th>Última OS</th><th class="text-end">Ação</th></tr></thead><tbody>{% for customer in customers %}<tr><td>{{ customer.name }}</td><td>{{ customer.phone }}</td><td>{{ customer.email|default:"-" }}</td><td>{{ customer.last_order_at|date:"d/m/Y"|default:"Sem OS" }}</td><td class="text-end"><a class="btn btn-sm btn-outline-primary" href="{% url 'crm:interaction_create' %}?customer={{ customer.pk }}">Registrar contato</a></td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted py-4">Nenhum cliente inativo encontrado.</td></tr>{% endfor %}</tbody></table></div></div></div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/inactive_customer_list.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}

{% block title %}Interações - CRM{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div><h1 class="h4 mb-1">Interações</h1><p class="text-muted mb-0">Histórico auditável de relacionamento com clientes.</p></div>
    <a href="{% url 'crm:interaction_create' %}" class="btn btn-primary">Nova interação</a>
</div>
<form method="get" class="card card-body shadow-sm mb-3"><div class="input-group"><input type="text" name="search" value="{{ search }}" class="form-control" placeholder="Buscar por cliente, assunto ou descrição"><button class="btn btn-outline-secondary" type="submit">Buscar</button></div></form>
<div class="card shadow-sm"><div class="card-body"><div class="table-responsive"><table class="table table-hover align-middle">
<thead><tr><th>Data</th><th>Cliente</th><th>OS</th><th>Tipo</th><th>Canal</th><th>Assunto</th><th>Follow-up</th></tr></thead>
<tbody>{% for interaction in interactions %}<tr><td>{{ interaction.interaction_date|date:"d/m/Y H:i" }}</td><td><a href="{% url 'customers:customer_detail' interaction.customer.pk %}">{{ interaction.customer.name }}</a></td><td>{% if interaction.service_order %}<a href="{% url 'service_orders:service_order_detail' interaction.service_order.pk %}">#{{ interaction.service_order.pk }}</a>{% else %}-{% endif %}</td><td>{{ interaction.get_interaction_type_display }}</td><td>{{ interaction.get_channel_display }}</td><td>{{ interaction.subject }}</td><td>{{ interaction.next_follow_up_date|date:"d/m/Y"|default:"-" }}</td></tr>{% empty %}<tr><td colspan="7" class="text-center text-muted py-4">Nenhuma interação encontrada.</td></tr>{% endfor %}</tbody>
</table></div></div></div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/interaction_list.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% block title %}Oportunidades - CRM{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4"><div><h1 class="h4 mb-1">Oportunidades</h1><p class="text-muted mb-0">Pipeline comercial do relacionamento com clientes.</p></div><a href="{% url 'crm:opportunity_create' %}" class="btn btn-primary">Nova oportunidade</a></div>
<form method="get" class="card card-body shadow-sm mb-3"><select name="status" class="form-select" onchange="this.form.submit()"><option value="">Todos os status</option>{% for value,label in status_choices %}<option value="{{ value }}" {% if status == value %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></form>
<div class="card shadow-sm"><div class="card-body"><div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th>Título</th><th>Cliente</th><th>Status</th><th>Valor estimado</th><th>Probabilidade</th><th>Previsão</th></tr></thead><tbody>{% for opportunity in opportunities %}<tr><td>{{ opportunity.title }}</td><td>{{ opportunity.customer.name }}</td><td>{{ opportunity.get_status_display }}</td><td>R$ {{ opportunity.estimated_value }}</td><td>{{ opportunity.probability }}%</td><td>{{ opportunity.expected_close_date|date:"d/m/Y"|default:"-" }}</td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted py-4">Nenhuma oportunidade encontrada.</td></tr>{% endfor %}</tbody></table></div></div></div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/opportunity_list.html"

New-Item -ItemType Directory -Force -Path "templates/crm" | Out-Null

@'
{% extends "base.html" %}
{% block title %}Lembretes - CRM{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4"><div><h1 class="h4 mb-1">Lembretes e follow-ups</h1><p class="text-muted mb-0">Ações pendentes de relacionamento.</p></div><a href="{% url 'crm:reminder_create' %}" class="btn btn-primary">Novo lembrete</a></div>
<form method="get" class="card card-body shadow-sm mb-3"><select name="status" class="form-select" onchange="this.form.submit()"><option value="">Todos os status</option>{% for value,label in status_choices %}<option value="{{ value }}" {% if status == value %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></form>
<div class="card shadow-sm"><div class="card-body"><div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th>Data</th><th>Cliente</th><th>Título</th><th>Status</th><th>Responsável</th><th class="text-end">Ação</th></tr></thead><tbody>{% for reminder in reminders %}<tr><td>{{ reminder.due_date|date:"d/m/Y" }}</td><td>{{ reminder.customer.name }}</td><td>{{ reminder.title }}</td><td>{{ reminder.get_status_display }}</td><td>{{ reminder.responsible_user|default:"-" }}</td><td class="text-end">{% if reminder.status == "pending" %}<form method="post" action="{% url 'crm:reminder_done' reminder.pk %}">{% csrf_token %}<button type="submit" class="btn btn-sm btn-success">Concluir</button></form>{% endif %}</td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted py-4">Nenhum lembrete encontrado.</td></tr>{% endfor %}</tbody></table></div></div></div>
{% endblock %}

'@ | Set-Content -Encoding UTF8 "templates/crm/reminder_list.html"

Write-Host "CRM aplicado. Agora execute: python manage.py migrate"