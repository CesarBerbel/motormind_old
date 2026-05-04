from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("assistente/", views.assistant, name="assistant"),
    path("respostas/<int:pk>/", views.response_detail, name="response_detail"),
]
