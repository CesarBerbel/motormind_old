from decimal import Decimal

from django import forms

from inventory.models import Part


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

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o nome da peça",
                }
            ),
            "internal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: BRK-001",
                }
            ),
            "barcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o código de barras",
                }
            ),
            "brand": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a marca",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Freio, Motor, Suspensão",
                }
            ),
            "unit": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: un, lt, kg",
                }
            ),
            "cost_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Ex: 80,00",
                }
            ),
            "sale_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Ex: 150,00",
                }
            ),
            "current_stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Ex: 10",
                }
            ),
            "minimum_stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Ex: 3",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Prateleira A1",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

        labels = {
            "name": "Nome da peça",
            "internal_code": "Código interno",
            "barcode": "Código de barras",
            "brand": "Marca",
            "category": "Categoria",
            "unit": "Unidade",
            "cost_price": "Preço de custo",
            "sale_price": "Preço de venda",
            "current_stock": "Estoque atual",
            "minimum_stock": "Estoque mínimo",
            "location": "Localização",
            "is_active": "Ativa",
        }


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
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
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
