from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from core.form_fields import BRLDecimalField, money_widget
from workshop_services.models import (
    ServiceCombo,
    ServiceComboItem,
    WorkshopService,
    WorkshopServiceCategory,
    WorkshopServicePart,
)


COMPACT_TEXT_ATTRS = {
    "class": "form-control form-control-sm",
    "autocomplete": "off",
}
COMPACT_SELECT_ATTRS = {"class": "form-select form-select-sm"}
COMPACT_NUMBER_ATTRS = {"class": "form-control form-control-sm"}


def compact_money_widget(placeholder="Ex: R$ 150,00"):
    widget = money_widget(placeholder)
    widget.attrs["class"] = "form-control form-control-sm money-input"
    return widget


class WorkshopServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = WorkshopServiceCategory
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class WorkshopServiceForm(forms.ModelForm):
    default_price = BRLDecimalField(
        label="Preço padrão",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=compact_money_widget("Ex: R$ 180,00"),
    )

    class Meta:
        model = WorkshopService
        fields = [
            "name",
            "code",
            "category",
            "description",
            "default_price",
            "estimated_minutes",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "code": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "category": forms.Select(attrs=COMPACT_SELECT_ATTRS),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3}
            ),
            "estimated_minutes": forms.NumberInput(
                attrs={**COMPACT_NUMBER_ATTRS, "min": "0"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = WorkshopServiceCategory.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["category"].required = False


class WorkshopServicePartForm(forms.ModelForm):
    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=compact_money_widget("Vazio = preço de venda da peça"),
    )

    class Meta:
        model = WorkshopServicePart
        fields = ["part", "quantity", "unit_price", "is_active"]
        widgets = {
            "part": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "step": "0.01",
                    "min": "0.01",
                    "inputmode": "decimal",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


WorkshopServicePartFormSet = inlineformset_factory(
    WorkshopService,
    WorkshopServicePart,
    form=WorkshopServicePartForm,
    extra=0,
    can_delete=True,
)


class ServiceComboForm(forms.ModelForm):
    discount_amount = BRLDecimalField(
        label="Desconto do combo",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=compact_money_widget("Ex: R$ 50,00"),
    )

    class Meta:
        model = ServiceCombo
        fields = [
            "name",
            "code",
            "description",
            "discount_amount",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "code": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_discount_amount(self):
        return self.cleaned_data.get("discount_amount") or Decimal("0.00")


class ServiceComboItemForm(forms.ModelForm):
    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=compact_money_widget("Ex: R$ 120,00"),
    )

    class Meta:
        model = ServiceComboItem
        fields = ["service", "quantity", "unit_price"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "step": "0.01",
                    "min": "0.01",
                    "inputmode": "decimal",
                }
            ),
        }


ServiceComboItemFormSet = inlineformset_factory(
    ServiceCombo,
    ServiceComboItem,
    form=ServiceComboItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class AddCatalogServiceToOrderForm(forms.Form):
    service = forms.ModelChoiceField(
        label="Serviço",
        queryset=WorkshopService.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.DecimalField(
        label="Quantidade",
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        initial=Decimal("1.00"),
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
        ),
    )
    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=money_widget("Deixe vazio para usar o preço padrão"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = WorkshopService.objects.filter(
            is_active=True
        ).order_by("name")


class AddComboToOrderForm(forms.Form):
    combo = forms.ModelChoiceField(
        label="Combo",
        queryset=ServiceCombo.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["combo"].queryset = (
            ServiceCombo.objects.filter(is_active=True)
            .prefetch_related(
                "items",
                "items__service",
            )
            .order_by("name")
        )
