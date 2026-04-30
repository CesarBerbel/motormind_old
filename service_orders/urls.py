from django.urls import path

from . import views

app_name = "service_orders"


urlpatterns = [
    path(
        "ordens/",
        views.service_order_list_view,
        name="service_order_list",
    ),
    path(
        "ordens/criar/",
        views.service_order_create_view,
        name="service_order_create",
    ),
    path(
        "ordens/<int:pk>/",
        views.service_order_detail_view,
        name="service_order_detail",
    ),
    path(
        "ordens/<int:pk>/editar/",
        views.service_order_update_view,
        name="service_order_update",
    ),
    path(
        "ordens/<int:pk>/tecnico/",
        views.service_order_technical_update_view,
        name="service_order_technical_update",
    ),
    path(
        "ordens/<int:pk>/excluir/",
        views.service_order_delete_view,
        name="service_order_delete",
    ),
]
