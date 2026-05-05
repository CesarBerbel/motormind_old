from django.urls import path

from workshop_services import views

app_name = "workshop_services"

urlpatterns = [
    path("", views.service_catalog_list_view, name="service_catalog_list"),
    path("criar/", views.service_create_view, name="service_create"),
    path("<int:pk>/editar/", views.service_update_view, name="service_update"),
    path("combos/criar/", views.combo_create_view, name="combo_create"),
    path("combos/<int:pk>/editar/", views.combo_update_view, name="combo_update"),
    path("ordens/<int:service_order_pk>/adicionar-servico/", views.add_service_to_order_view, name="add_service_to_order"),
    path("ordens/<int:service_order_pk>/adicionar-combo/", views.add_combo_to_order_view, name="add_combo_to_order"),
]
