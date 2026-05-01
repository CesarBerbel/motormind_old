from django.urls import path

from inventory.views import part_views, service_order_part_views

app_name = "inventory"


urlpatterns = [
    path(
        "pecas/",
        part_views.part_list_view,
        name="part_list",
    ),
    path(
        "pecas/criar/",
        part_views.part_create_view,
        name="part_create",
    ),
    path(
        "pecas/<int:pk>/",
        part_views.part_detail_view,
        name="part_detail",
    ),
    path(
        "pecas/<int:pk>/editar/",
        part_views.part_update_view,
        name="part_update",
    ),
    path(
        "pecas/<int:pk>/movimentar/",
        part_views.stock_movement_create_view,
        name="stock_movement_create",
    ),
    path(
        "ordens/<int:service_order_pk>/pecas/adicionar/",
        service_order_part_views.service_order_part_add_view,
        name="service_order_part_add",
    ),
    path(
        "ordens/<int:service_order_pk>/pecas/<int:pk>/confirmar-uso/",
        service_order_part_views.service_order_part_confirm_usage_view,
        name="service_order_part_confirm_usage",
    ),
    path(
        "ordens/<int:service_order_pk>/pecas/<int:pk>/cancelar/",
        service_order_part_views.service_order_part_cancel_view,
        name="service_order_part_cancel",
    ),
    path(
        "ordens/<int:service_order_pk>/pecas/<int:pk>/devolver/",
        service_order_part_views.service_order_part_return_view,
        name="service_order_part_return",
    ),
]
