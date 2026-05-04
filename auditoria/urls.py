from django.urls import path

from auditoria import views

app_name = "auditoria"

urlpatterns = [
    path("", views.audit_log_list, name="audit_log_list"),
    path("<int:pk>/", views.audit_log_detail, name="audit_log_detail"),
]
