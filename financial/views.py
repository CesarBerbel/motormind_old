from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.exceptions import DomainError
from core.permissions import (
    can_manage_financial,
    can_view_financial,
    user_passes_permission,
)

from .forms import ExpenseForm, ExpensePaymentForm, PaymentForm, ReceivableCreateForm
from .models import PaymentStatus
from .selectors import (
    get_cash_flow_entries,
    get_expense_by_id,
    get_expenses_for_list,
    get_financial_dashboard_data,
    get_receivable_by_id,
    get_receivables_for_list,
)
from .services import (
    create_receivable_from_service_order,
    mark_expense_as_paid,
    register_expense,
    register_payment,
)


@login_required
@user_passes_permission(can_view_financial)
def dashboard(request):
    """
    Render financial dashboard.
    """
    context = get_financial_dashboard_data(
        {
            "start_date": request.GET.get("start_date"),
            "end_date": request.GET.get("end_date"),
        }
    )
    context["filters"] = {
        "start_date": request.GET.get("start_date", ""),
        "end_date": request.GET.get("end_date", ""),
    }

    return render(request, "financial/dashboard.html", context)


@login_required
@user_passes_permission(can_view_financial)
def receivable_list_view(request):
    """
    List receivables with basic filters.
    """
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    context = {
        "receivables": get_receivables_for_list(search=search, status=status),
        "payment_status_choices": PaymentStatus.choices,
        "filters": {
            "q": search,
            "status": status,
        },
    }

    return render(request, "financial/receivable_list.html", context)


@login_required
@user_passes_permission(can_view_financial)
def receivable_detail_view(request, pk):
    """
    Show one receivable and its payment history.
    """
    receivable = get_receivable_by_id(pk)

    return render(
        request,
        "financial/receivable_detail.html",
        {
            "receivable": receivable,
            "payments": receivable.payments.select_related("created_by").all(),
        },
    )


@login_required
@user_passes_permission(can_manage_financial)
def receivable_create_view(request):
    """
    Create a receivable from a finished service order.
    """
    if request.method == "POST":
        form = ReceivableCreateForm(request.POST)

        if form.is_valid():
            try:
                receivable = create_receivable_from_service_order(
                    service_order=form.cleaned_data["service_order"],
                    due_date=form.cleaned_data["due_date"],
                    created_by=request.user,
                )
            except DomainError as exc:
                messages.error(request, exc.message)
            else:
                messages.success(request, "Conta a receber criada com sucesso.")
                return redirect("financial:receivable_detail", pk=receivable.pk)
    else:
        form = ReceivableCreateForm()

    return render(
        request,
        "financial/receivable_form.html",
        {
            "form": form,
            "title": "Nova conta a receber",
            "submit_label": "Criar conta a receber",
        },
    )


@login_required
@user_passes_permission(can_manage_financial)
def payment_create_view(request, receivable_pk):
    """
    Register a payment for a receivable.
    """
    receivable = get_receivable_by_id(receivable_pk)

    if receivable.status == PaymentStatus.PAID:
        messages.info(request, "Esta conta já está paga.")
        return redirect("financial:receivable_detail", pk=receivable.pk)

    if request.method == "POST":
        form = PaymentForm(request.POST, receivable=receivable)

        if form.is_valid():
            try:
                register_payment(
                    receivable=receivable,
                    amount=form.cleaned_data["amount"],
                    method=form.cleaned_data["method"],
                    paid_at=form.cleaned_data["paid_at"],
                    notes=form.cleaned_data["notes"],
                    created_by=request.user,
                )
            except DomainError as exc:
                messages.error(request, exc.message)
            else:
                messages.success(request, "Pagamento registrado com sucesso.")
                return redirect("financial:receivable_detail", pk=receivable.pk)
    else:
        form = PaymentForm(
            receivable=receivable, initial={"amount": receivable.remaining_amount}
        )

    return render(
        request,
        "financial/payment_form.html",
        {
            "form": form,
            "receivable": receivable,
            "title": "Registrar pagamento",
            "submit_label": "Registrar pagamento",
        },
    )


@login_required
@user_passes_permission(can_view_financial)
def expense_list_view(request):
    """
    List expenses with basic filters.
    """
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    context = {
        "expenses": get_expenses_for_list(search=search, status=status),
        "payment_status_choices": PaymentStatus.choices,
        "filters": {
            "q": search,
            "status": status,
        },
    }

    return render(request, "financial/expense_list.html", context)


@login_required
@user_passes_permission(can_manage_financial)
def expense_create_view(request):
    """
    Create an expense.
    """
    if request.method == "POST":
        form = ExpenseForm(request.POST)

        if form.is_valid():
            try:
                expense = register_expense(
                    description=form.cleaned_data["description"],
                    amount=form.cleaned_data["amount"],
                    due_date=form.cleaned_data["due_date"],
                    paid_at=form.cleaned_data["paid_at"],
                    notes=form.cleaned_data["notes"],
                    created_by=request.user,
                )
            except DomainError as exc:
                messages.error(request, exc.message)
            else:
                messages.success(
                    request, f"Despesa '{expense.description}' criada com sucesso."
                )
                return redirect("financial:expense_list")
    else:
        form = ExpenseForm()

    return render(
        request,
        "financial/expense_form.html",
        {
            "form": form,
            "title": "Nova despesa",
            "submit_label": "Salvar despesa",
        },
    )


@login_required
@user_passes_permission(can_manage_financial)
def expense_pay_view(request, pk):
    """
    Mark an expense as paid.
    """
    expense = get_expense_by_id(pk)

    if expense.status == PaymentStatus.PAID:
        messages.info(request, "Esta despesa já está paga.")
        return redirect("financial:expense_list")

    if request.method == "POST":
        form = ExpensePaymentForm(request.POST)

        if form.is_valid():
            try:
                mark_expense_as_paid(
                    expense=expense,
                    paid_at=form.cleaned_data["paid_at"],
                    user=request.user,
                )
            except DomainError as exc:
                messages.error(request, exc.message)
            else:
                messages.success(request, "Despesa marcada como paga.")
                return redirect("financial:expense_list")
    else:
        form = ExpensePaymentForm()

    return render(
        request,
        "financial/expense_pay_form.html",
        {
            "form": form,
            "expense": expense,
            "title": "Marcar despesa como paga",
            "submit_label": "Confirmar pagamento",
        },
    )


@login_required
@user_passes_permission(can_view_financial)
def cash_flow_list_view(request):
    """
    List cash flow entries.
    """
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    return render(
        request,
        "financial/cash_flow_list.html",
        {
            "cash_flow_entries": get_cash_flow_entries(
                start_date=start_date,
                end_date=end_date,
            ),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
            },
        },
    )
