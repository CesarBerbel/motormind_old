from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from core.form_fields import BRLDecimalField, money_widget
from workshop_services.models import ServiceCombo, ServiceComboItem, WorkshopService


class WorkshopServiceForm(forms.ModelForm):
    default_price = BRLDecimalField(
        label="Preço padrão",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=money_widget("Ex: R$ 180,00"),
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
            "name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "code": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "category": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "estimated_minutes": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ServiceComboForm(forms.ModelForm):
    discount_amount = BRLDecimalField(
        label="Desconto do combo",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 50,00"),
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
            "name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "code": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
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
        widget=money_widget("Ex: R$ 120,00"),
    )

    class Meta:
        model = ServiceComboItem
        fields = ["service", "quantity", "unit_price"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
        }


ServiceComboItemFormSet = inlineformset_factory(
    ServiceCombo,
    ServiceComboItem,
    form=ServiceComboItemForm,
    extra=1,
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
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
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
        self.fields["service"].queryset = WorkshopService.objects.filter(is_active=True).order_by("name")


class AddComboToOrderForm(forms.Form):
    combo = forms.ModelChoiceField(
        label="Combo",
        queryset=ServiceCombo.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["combo"].queryset = ServiceCombo.objects.filter(is_active=True).prefetch_related(
            "items",
            "items__service",
        ).order_by("name")
