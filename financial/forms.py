from decimal import Decimal

from django import forms
from django.utils import timezone

from service_orders.models import ServiceOrder

from .models import Expense, PaymentMethod


class ReceivableCreateForm(forms.Form):
    """
    Form used to create a receivable from a finished service order.
    """

    service_order = forms.ModelChoiceField(
        queryset=ServiceOrder.objects.none(),
        label="Ordem de serviço",
        help_text="Selecione uma OS finalizada que ainda não possui conta a receber.",
    )
    due_date = forms.DateField(
        label="Data de vencimento",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_order"].queryset = (
            ServiceOrder.objects.select_related("customer", "vehicle")
            .filter(status=ServiceOrder.Status.FINISHED)
            .filter(receivable__isnull=True)
            .order_by("-finished_at", "-created_at")
        )


class PaymentForm(forms.Form):
    """
    Form used to register a payment for a receivable.
    """

    amount = forms.DecimalField(
        label="Valor pago",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    method = forms.ChoiceField(
        label="Forma de pagamento",
        choices=PaymentMethod.choices,
    )
    paid_at = forms.DateTimeField(
        label="Pago em",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Se ficar em branco, o sistema usará a data e hora atual.",
    )
    notes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, receivable=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.receivable = receivable
        self.fields["amount"].widget.attrs.update({"step": "0.01"})

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if self.receivable and amount > self.receivable.remaining_amount:
            raise forms.ValidationError(
                "O pagamento não pode ser maior que o saldo em aberto."
            )

        return amount

    def clean_paid_at(self):
        return self.cleaned_data.get("paid_at") or timezone.now()


class ExpenseForm(forms.ModelForm):
    """
    Form used to create workshop expenses.
    """

    class Meta:
        model = Expense
        fields = [
            "description",
            "amount",
            "due_date",
            "paid_at",
            "notes",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "paid_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs.update({"step": "0.01"})
        self.fields["paid_at"].help_text = "Preencha somente se a despesa já foi paga."


class ExpensePaymentForm(forms.Form):
    """
    Form used to mark an existing expense as paid.
    """

    paid_at = forms.DateTimeField(
        label="Pago em",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Se ficar em branco, o sistema usará a data e hora atual.",
    )

    def clean_paid_at(self):
        return self.cleaned_data.get("paid_at") or timezone.now()
