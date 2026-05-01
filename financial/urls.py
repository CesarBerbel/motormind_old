from django.urls import path

from . import views

app_name = "financial"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
