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
        "quadro/",
        views.service_order_board_view,
        name="service_order_board",
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
        "ordens/<int:pk>/cancelar/",
        views.service_order_cancel_view,
        name="service_order_cancel",
    ),
    path(
        "ordens/<int:pk>/itens/adicionar/",
        views.service_order_item_add_view,
        name="service_order_item_add",
    ),
    path(
        "ordens/<int:pk>/itens/<int:item_pk>/editar/",
        views.service_order_item_update_view,
        name="service_order_item_update",
    ),
    path(
        "ordens/<int:pk>/itens/<int:item_pk>/excluir/",
        views.service_order_item_delete_view,
        name="service_order_item_delete",
    ),
    path(
        "ordens/<int:pk>/observacoes/adicionar/",
        views.service_order_note_create_view,
        name="service_order_note_create",
    ),
    path(
        "ajax/veiculos-por-cliente/",
        views.vehicles_by_customer_view,
        name="vehicles_by_customer",
    ),
]
