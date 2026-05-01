from decimal import Decimal

from django import forms

from .models import Part, ServiceOrderPart, StockMovement


class PartForm(forms.ModelForm):
    """Form to create and update parts."""

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
            "minimum_stock",
            "location",
            "is_active",
        ]
        widgets = {
            # Standard Bootstrap classes for all fields
            field: forms.TextInput(attrs={"class": "form-control"})
            for field in fields
        }


class StockMovementForm(forms.ModelForm):
    """
    Form for manual stock adjustments and movements.
    Enforces audit reasoning.
    """

    class Meta:
        model = StockMovement
        fields = ["movement_type", "quantity", "reason"]
        widgets = {
            "movement_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descreva detalhadamente o motivo (Ex: Contagem física, Peça avariada...)",
                }
            ),
        }

    def clean_reason(self):
        """Mandatory 5-character reason check."""
        reason = self.cleaned_data.get("reason")
        if not reason or len(reason.strip()) < 5:
            raise forms.ValidationError(
                "Para auditoria, a justificativa deve ter no mínimo 5 caracteres."
            )
        return reason


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
