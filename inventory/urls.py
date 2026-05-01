from django.urls import path

from inventory.views import part_views

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
]
