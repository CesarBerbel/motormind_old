from django.urls import path

from . import views

app_name = "financial"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("contas-a-receber/", views.receivable_list_view, name="receivable_list"),
    path(
        "contas-a-receber/nova/", views.receivable_create_view, name="receivable_create"
    ),
    path(
        "contas-a-receber/<int:pk>/",
        views.receivable_detail_view,
        name="receivable_detail",
    ),
    path(
        "contas-a-receber/<int:receivable_pk>/pagamentos/novo/",
        views.payment_create_view,
        name="payment_create",
    ),
    path("despesas/", views.expense_list_view, name="expense_list"),
    path("despesas/nova/", views.expense_create_view, name="expense_create"),
    path("despesas/<int:pk>/pagar/", views.expense_pay_view, name="expense_pay"),
    path("fluxo-caixa/", views.cash_flow_list_view, name="cash_flow_list"),
]
