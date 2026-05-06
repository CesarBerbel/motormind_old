from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory, modelformset_factory

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


class ServicePriceSelect(forms.Select):
    """
    Select de servicos que expõe o preco padrao no option.

    O JavaScript do formulario de combo usa estes atributos para preencher
    automaticamente o preco unitario quando o servico for escolhido.
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        instance = getattr(value, "instance", None)
        if instance is not None:
            default_price = instance.default_price or Decimal("0.00")
            option["attrs"]["data-default-price"] = f"{default_price:.2f}"

        return option


class WorkshopServiceCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = WorkshopServiceCategory.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["parent"].required = False
        if self.instance and self.instance.pk:
            self.fields["parent"].queryset = self.fields["parent"].queryset.exclude(
                pk=self.instance.pk
            )

    class Meta:
        model = WorkshopServiceCategory
        fields = ["name", "parent", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
            "parent": forms.Select(attrs=COMPACT_SELECT_ATTRS),
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


class ServiceComboForm(forms.Form):
    """
    Formulario principal do combo sem ModelForm.

    Motivo:
    na criacao do combo, o ServiceCombo ainda nao possui primary key.
    Se o ModelForm chamar validacoes do model e alguma regra do model acessar
    combo.items, o Django dispara:

    "ServiceCombo instance needs to have a primary key value before this relationship can be used."

    Este forms.Form valida apenas os campos simples do combo e salva o objeto
    manualmente. Os itens/servicos do combo continuam sendo salvos pelo formset.
    """

    name = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
    )
    code = forms.CharField(
        label="Codigo",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs=COMPACT_TEXT_ATTRS),
    )
    description = forms.CharField(
        label="Descricao",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control form-control-sm", "rows": 3}
        ),
    )
    discount_amount = BRLDecimalField(
        label="Desconto do combo",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=compact_money_widget("Ex: R$ 50,00"),
    )
    is_active = forms.BooleanField(
        label="Ativo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        initial = kwargs.pop("initial", {}) or {}

        if instance is not None and not args:
            initial.update(
                {
                    "name": instance.name,
                    "code": instance.code,
                    "description": instance.description,
                    "discount_amount": instance.discount_amount,
                    "is_active": instance.is_active,
                }
            )

        super().__init__(*args, initial=initial, **kwargs)

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code:
            return code

        qs = ServiceCombo.objects.filter(code__iexact=code)
        if self.instance is not None and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "Ja existe um combo cadastrado com este codigo."
            )

        return code

    def clean_discount_amount(self):
        return self.cleaned_data.get("discount_amount") or Decimal("0.00")

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Nao e possivel salvar um formulario invalido.")

        combo = self.instance or ServiceCombo()
        combo.name = self.cleaned_data["name"]
        combo.code = self.cleaned_data.get("code", "")
        combo.description = self.cleaned_data.get("description", "")
        combo.discount_amount = self.cleaned_data.get("discount_amount") or Decimal(
            "0.00"
        )
        combo.is_active = self.cleaned_data.get("is_active", False)

        if commit:
            combo.save()

        return combo


class ServiceComboItemForm(forms.ModelForm):
    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=compact_money_widget("Preenchido pelo serviço"),
    )

    class Meta:
        model = ServiceComboItem
        fields = ["service", "quantity", "unit_price"]
        widgets = {
            "service": ServicePriceSelect(
                attrs={"class": "form-select form-select-sm combo-service-select"}
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "step": "0.01",
                    "min": "0.01",
                    "inputmode": "decimal",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = WorkshopService.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["unit_price"].widget.attrs["class"] = (
            self.fields["unit_price"].widget.attrs.get("class", "")
            + " combo-service-price-input"
        ).strip()


ServiceComboItemFormSet = inlineformset_factory(
    ServiceCombo,
    ServiceComboItem,
    form=ServiceComboItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

# Usado exclusivamente na tela de criação do combo.
# Motivo: inlineformset_factory precisa acessar combo.items e isso falha
# quando o ServiceCombo ainda não possui primary key.
# O modelformset não depende de instance antes de salvar o combo.
ServiceComboItemCreateFormSet = modelformset_factory(
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
