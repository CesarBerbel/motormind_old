from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("clientes/", views.customer_list_view, name="customer_list"),
    path("clientes/cadastrar/", views.customer_create_view, name="customer_create"),
    path("clientes/<int:pk>/", views.customer_detail_view, name="customer_detail"),
    path("clientes/<int:pk>/editar/", views.customer_update_view, name="customer_update"),
    path("clientes/<int:pk>/excluir/", views.customer_delete_view, name="customer_delete"),
    path("clientes/<int:pk>/restaurar/", views.customer_restore_view, name="customer_restore"),
    path("veiculos/", views.vehicle_list_view, name="vehicle_list"),
    path("veiculos/cadastrar/", views.vehicle_create_view, name="vehicle_create"),
    path("veiculos/<int:pk>/editar/", views.vehicle_update_view, name="vehicle_update"),
    path("veiculos/<int:pk>/excluir/", views.vehicle_delete_view, name="vehicle_delete"),
    path("veiculos/<int:pk>/restaurar/", views.vehicle_restore_view, name="vehicle_restore"),
]
