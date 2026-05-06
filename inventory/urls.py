from django.urls import path

from inventory.views import part_views, service_order_part_views

app_name = "inventory"


urlpatterns = [
    path(
        "marcas/",
        part_views.brand_list_view,
        name="brand_list",
    ),
    path(
        "marcas/criar/",
        part_views.brand_create_view,
        name="brand_create",
    ),
    path(
        "marcas/<int:pk>/editar/",
        part_views.brand_update_view,
        name="brand_update",
    ),
    path(
        "categorias/",
        part_views.category_list_view,
        name="category_list",
    ),
    path(
        "categorias/criar/",
        part_views.category_create_view,
        name="category_create",
    ),
    path(
        "categorias/<int:pk>/editar/",
        part_views.category_update_view,
        name="category_update",
    ),
    path(
        "pecas/",
        part_views.part_list_view,
        name="part_list",
    ),
    path(
        "pecas/criticas/",
        part_views.critical_parts_view,
        name="critical_parts",
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
    path("pecas/autocomplete/", part_views.part_autocomplete, name="part_autocomplete"),
]
