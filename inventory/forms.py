from decimal import Decimal

from django import forms

from core.form_fields import BRLDecimalField, money_widget

from .models import Part, ServiceOrderPart, StockMovement


class PartForm(forms.ModelForm):
    """
    Form to create and update inventory parts.
    """

    cost_price = BRLDecimalField(
        label="Preço de custo",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 80,00"),
    )

    sale_price = BRLDecimalField(
        label="Preço de venda",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 150,00"),
    )

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
                    "placeholder": "Ex: Pastilha de freio dianteira",
                    "autocomplete": "off",
                }
            ),
            "internal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: BRK-001",
                    "autocomplete": "off",
                }
            ),
            "barcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código de barras, se houver",
                    "autocomplete": "off",
                }
            ),
            "brand": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Bosch",
                    "autocomplete": "off",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Freio, Motor, Suspensão",
                    "autocomplete": "off",
                }
            ),
            "unit": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: un, par, litro, kit",
                    "autocomplete": "off",
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
                    "autocomplete": "off",
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
            "current_stock": "Estoque atual",
            "minimum_stock": "Estoque mínimo",
            "location": "Localização",
            "is_active": "Peça ativa",
        }

        help_texts = {
            "internal_code": "Código único usado internamente para localizar a peça.",
            "current_stock": "Quantidade disponível no estoque no momento do cadastro.",
            "minimum_stock": "Quando o estoque atual ficar igual ou abaixo deste valor, a peça será considerada crítica.",
        }

    def clean_cost_price(self):
        return self.cleaned_data.get("cost_price") or Decimal("0.00")

    def clean_sale_price(self):
        return self.cleaned_data.get("sale_price") or Decimal("0.00")


class StockMovementForm(forms.ModelForm):
    """
    Form for manual stock adjustments and movements.
    """

    class Meta:
        model = StockMovement
        fields = [
            "movement_type",
            "quantity",
            "reason",
        ]

        widgets = {
            "movement_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Informe a quantidade",
                }
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Ex: Entrada por compra, perda por avaria ou ajuste após contagem física",
                }
            ),
        }

        labels = {
            "movement_type": "Tipo de movimentação",
            "quantity": "Quantidade",
            "reason": "Justificativa",
        }

        help_texts = {
            "quantity": "Para ajuste, informe o novo saldo final da peça.",
            "reason": "A justificativa é obrigatória para auditoria do estoque.",
        }

    def clean_reason(self):
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

    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=money_widget("Ex: R$ 150,00"),
    )

    discount = BRLDecimalField(
        label="Desconto",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 10,00"),
    )

    class Meta:
        model = ServiceOrderPart
        fields = [
            "part",
            "quantity",
            "unit_price",
            "discount",
        ]

        widgets = {
            "part": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Digite a quantidade",
                }
            ),
        }

        labels = {
            "part": "Peça",
            "quantity": "Quantidade",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["part"].queryset = Part.objects.filter(is_active=True).order_by(
            "name"
        )

    def clean_discount(self):
        return self.cleaned_data.get("discount") or Decimal("0.00")

    def clean(self):
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
