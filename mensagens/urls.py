from django.urls import path

from . import views

app_name = "mensagens"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("templates/", views.template_list, name="template_list"),
    path("templates/novo/", views.template_create, name="template_create"),
    path("templates/<int:pk>/editar/", views.template_update, name="template_update"),
    path("variaveis/", views.variable_help, name="variable_help"),
    path("preview/", views.message_preview_view, name="message_preview"),
    path("manual/nova/", views.manual_message_create, name="manual_message_create"),
    path("fila/", views.queue_list, name="queue_list"),
    path("fila/<int:pk>/processar/", views.queue_process, name="queue_process"),
    path("logs/", views.log_list, name="log_list"),
]
