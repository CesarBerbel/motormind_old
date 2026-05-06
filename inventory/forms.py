from decimal import Decimal

from django import forms

from core.form_fields import BRLDecimalField, money_widget

from .models import Part, PartBrand, PartCategory, ServiceOrderPart, StockMovement


class PartForm(forms.ModelForm):
    """
    Form to create and update inventory parts.
    Accepts brand and category as text and converts them to related model instances.
    """

    brand = forms.CharField(
        label="Marca",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex: Bosch",
                "autocomplete": "off",
            }
        ),
    )

    category = forms.CharField(
        label="Categoria",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex: Freio, Motor, Suspensão",
                "autocomplete": "off",
            }
        ),
    )

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
                }
            ),
            "internal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: BRK-001"}
            ),
            "barcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código de barras, se houver",
                }
            ),
            "unit": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: un, par, litro, kit",
                }
            ),
            "current_stock": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "minimum_stock": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: Prateleira A1"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_brand(self):
        brand_name = (self.cleaned_data.get("brand") or "").strip()

        if not brand_name:
            return None

        brand, _created = PartBrand.objects.get_or_create(
            name=brand_name,
            defaults={"is_active": True},
        )

        return brand

    def clean_category(self):
        category_name = (self.cleaned_data.get("category") or "").strip()

        if not category_name:
            return None

        category, _created = PartCategory.objects.get_or_create(
            name=category_name,
            defaults={"is_active": True},
        )

        return category

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


class PartBrandForm(forms.ModelForm):
    """
    Form to create and update part brands.
    """

    class Meta:
        model = PartBrand
        fields = [
            "name",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Bosch, Cofap, Nakata",
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
            "name": "Nome da marca",
            "is_active": "Marca ativa",
        }
        help_texts = {
            "name": "Use um nome único para evitar marcas duplicadas no cadastro de peças.",
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        if not name:
            raise forms.ValidationError("Informe o nome da marca.")

        return name


class PartCategoryForm(forms.ModelForm):
    """
    Form to create and update part categories.
    """

    class Meta:
        model = PartCategory
        fields = [
            "name",
            "description",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Freios, Suspensão, Motor",
                    "autocomplete": "off",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descreva quais peças pertencem a esta categoria.",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "name": "Nome da categoria",
            "description": "Descrição",
            "is_active": "Categoria ativa",
        }
        help_texts = {
            "name": "Use categorias operacionais coerentes com o estoque da oficina.",
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        if not name:
            raise forms.ValidationError("Informe o nome da categoria.")

        return name
