from decimal import Decimal

from django import forms

from inventory.models import Part, ServiceOrderPart


class PartForm(forms.ModelForm):
    """
    Form used to create and update inventory parts.
    """

    class Meta:
        model = Part
        fields = [
            "name",
            "internal_code",
            "barcode",
            "brand",
            "category",
            "unit",
            "cost_price",
            "sale_price",
            "current_stock",
            "minimum_stock",
            "location",
            "is_active",
        ]


class StockMovementForm(forms.Form):
    """
    Form used to create stock movements.
    """

    movement_type = forms.ChoiceField(
        label="Tipo de movimentação",
        choices=[
            ("in", "Entrada"),
            ("out", "Saída"),
            ("loss", "Perda"),
            ("return", "Devolução"),
            ("reserve", "Reserva"),
            ("release", "Liberação de reserva"),
            ("adjust", "Ajuste"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    quantity = forms.DecimalField(
        label="Quantidade",
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "Digite a quantidade",
            }
        ),
    )

    reason = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Descreva o motivo da movimentação",
                "rows": 3,
            }
        ),
    )


class ServiceOrderPartForm(forms.ModelForm):
    """
    Form used to reserve an inventory part for a service order.
    """

    class Meta:
        model = ServiceOrderPart
        fields = [
            "part",
            "quantity",
            "unit_price",
            "discount",
        ]

        widgets = {
            "part": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Digite a quantidade",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Preço unitário",
                }
            ),
            "discount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Desconto",
                }
            ),
        }

        labels = {
            "part": "Peça",
            "quantity": "Quantidade",
            "unit_price": "Preço unitário",
            "discount": "Desconto",
        }

    def __init__(self, *args, **kwargs):
        """
        Limit parts to active parts.
        """
        super().__init__(*args, **kwargs)

        self.fields["part"].queryset = Part.objects.filter(is_active=True).order_by(
            "name"
        )

    def clean(self):
        """
        Validate discount against subtotal.
        """
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        unit_price = cleaned_data.get("unit_price")
        discount = cleaned_data.get("discount") or Decimal("0.00")

        if quantity and unit_price:
            subtotal = quantity * unit_price

            if discount > subtotal:
                raise forms.ValidationError(
                    "O desconto não pode ser maior que o subtotal da peça."
                )

        return cleaned_data
