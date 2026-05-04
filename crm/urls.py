from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("", views.crm_dashboard_view, name="dashboard"),
    path("interacoes/", views.interaction_list_view, name="interaction_list"),
    path("interacoes/nova/", views.interaction_create_view, name="interaction_create"),
    path("oportunidades/", views.opportunity_list_view, name="opportunity_list"),
    path(
        "oportunidades/nova/", views.opportunity_create_view, name="opportunity_create"
    ),
    path("lembretes/", views.reminder_list_view, name="reminder_list"),
    path("lembretes/novo/", views.reminder_create_view, name="reminder_create"),
    path(
        "lembretes/<int:pk>/concluir/", views.reminder_done_view, name="reminder_done"
    ),
    path(
        "clientes-inativos/",
        views.inactive_customer_list_view,
        name="inactive_customer_list",
    ),
    path("campanhas/", views.campaign_list_view, name="campaign_list"),
    path("campanhas/nova/", views.campaign_create_view, name="campaign_create"),
    path(
        "campanhas/<int:pk>/publico/adicionar/",
        views.campaign_audience_add_view,
        name="campaign_audience_add",
    ),
]
