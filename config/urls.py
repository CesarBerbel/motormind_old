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
    path(
        "mensagens/",
        include(("mensagens.urls", "mensagens"), namespace="mensagens"),
    ),
    path(
        "ia/",
        include(("ai.urls", "ai"), namespace="ai"),
    ),
]
