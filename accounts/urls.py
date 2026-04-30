from django.urls import path

from . import views

app_name = "accounts"


urlpatterns = [
    path(
        "cadastro/",
        views.register_view,
        name="register",
    ),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "painel/",
        views.dashboard_view,
        name="dashboard",
    ),
    path(
        "administracao/",
        views.admin_area_view,
        name="admin_area",
    ),
    path(
        "atendimento/",
        views.attendant_area_view,
        name="attendant_area",
    ),
    path(
        "mecanica/",
        views.mechanic_area_view,
        name="mechanic_area",
    ),
    path(
        "financeiro/",
        views.financial_area_view,
        name="financial_area",
    ),
    path(
        "sair/",
        views.logout_view,
        name="logout",
    ),
]
