from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.form_fields import BRLDecimalField, money_widget
from customers.models import Vehicle
from workshop_services.models import ServiceCombo, WorkshopService

from .models import (
    ServiceOrder,
    ServiceOrderApproval,
    ServiceOrderItem,
    ServiceOrderNote,
    ServiceOrderTimeEntry,
)
from .services import get_allowed_next_status_choices


class ServiceOrderForm(forms.ModelForm):
    labor_cost = BRLDecimalField(
        label="Valor da mão de obra",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 150,00"),
    )

    parts_cost = BRLDecimalField(
        label="Valor das peças",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 200,00"),
    )

    discount = BRLDecimalField(
        label="Desconto",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=money_widget("Ex: R$ 50,00"),
    )

    selected_services = forms.ModelMultipleChoiceField(
        label="Serviços",
        queryset=WorkshopService.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
    )

    selected_combos = forms.ModelMultipleChoiceField(
        label="Combos",
        queryset=ServiceCombo.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ServiceOrder
        fields = [
            "customer",
            "vehicle",
            "assigned_mechanic",
            "priority",
            "title",
            "description",
            "diagnosis",
            "solution",
            "status",
            "labor_cost",
            "parts_cost",
            "discount",
            "expected_delivery_date",
            "order_type",
            "warranty_origin_order",
            "warranty_reason",
        ]

        widgets = {
            "customer": forms.Select(
                attrs={"class": "form-select", "id": "id_customer"}
            ),
            "vehicle": forms.Select(attrs={"class": "form-select", "id": "id_vehicle"}),
            "assigned_mechanic": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite um título para a ordem de serviço",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o problema informado pelo cliente",
                    "rows": 4,
                }
            ),
            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o diagnóstico técnico",
                    "rows": 4,
                }
            ),
            "solution": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o serviço executado",
                    "rows": 4,
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "expected_delivery_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"},
            ),
            "order_type": forms.Select(attrs={"class": "form-select"}),
            "warranty_origin_order": forms.Select(attrs={"class": "form-select"}),
            "warranty_reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Informe o motivo da garantia ou retorno",
                }
            ),
        }

        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo",
            "assigned_mechanic": "Mecânico responsável",
            "priority": "Prioridade",
            "title": "Título",
            "description": "Descrição do problema",
            "diagnosis": "Diagnóstico técnico",
            "solution": "Serviço executado",
            "status": "Status",
            "expected_delivery_date": "Previsão de entrega",
            "order_type": "Tipo da OS",
            "warranty_origin_order": "OS original",
            "warranty_reason": "Motivo da garantia/retorno",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vehicle"].queryset = Vehicle.objects.none()

        self.fields["selected_services"].queryset = WorkshopService.objects.filter(
            is_active=True
        ).order_by("name")

        self.fields["selected_combos"].queryset = ServiceCombo.objects.filter(
            is_active=True
        ).order_by("name")

        if "warranty_origin_order" in self.fields:
            self.fields["warranty_origin_order"].required = False
            self.fields["warranty_origin_order"].queryset = (
                ServiceOrder.objects.all().order_by("-created_at")
            )

            if self.instance and self.instance.pk:
                self.fields["warranty_origin_order"].queryset = self.fields[
                    "warranty_origin_order"
                ].queryset.exclude(pk=self.instance.pk)

        if "warranty_reason" in self.fields:
            self.fields["warranty_reason"].required = False

        User = get_user_model()
        mechanic_group = Group.objects.filter(name="Mecânico").first()

        if mechanic_group:
            self.fields["assigned_mechanic"].queryset = User.objects.filter(
                groups=mechanic_group,
                is_active=True,
            ).order_by("first_name", "email")
        else:
            self.fields["assigned_mechanic"].queryset = User.objects.none()

        self.fields["assigned_mechanic"].required = False
        self.fields["assigned_mechanic"].empty_label = (
            "Selecione o mecânico responsável"
        )

        if self.instance and self.instance.pk:
            self.fields["status"].choices = get_allowed_next_status_choices(
                self.instance
            )
        else:
            self.fields["status"].choices = [
                (ServiceOrder.Status.OPEN, ServiceOrder.Status.OPEN.label),
            ]
            self.fields["status"].initial = ServiceOrder.Status.OPEN
            self.fields["status"].required = False

        if "customer" in self.data:
            try:
                customer_id = int(self.data.get("customer"))
                self.fields["vehicle"].queryset = Vehicle.objects.filter(
                    customer_id=customer_id,
                    is_active=True,
                ).order_by("plate")
            except (TypeError, ValueError):
                self.fields["vehicle"].queryset = Vehicle.objects.none()
        elif self.instance.pk and self.instance.customer_id:
            self.fields["vehicle"].queryset = Vehicle.objects.filter(
                customer_id=self.instance.customer_id,
                is_active=True,
            ).order_by("plate")

    def clean_labor_cost(self):
        return self.cleaned_data.get("labor_cost") or Decimal("0.00")

    def clean_parts_cost(self):
        return self.cleaned_data.get("parts_cost") or Decimal("0.00")

    def clean_discount(self):
        return self.cleaned_data.get("discount") or Decimal("0.00")

    def clean(self):
        cleaned_data = super().clean()

        customer = cleaned_data.get("customer")
        vehicle = cleaned_data.get("vehicle")
        order_type = cleaned_data.get("order_type")
        warranty_origin_order = cleaned_data.get("warranty_origin_order")
        warranty_reason = cleaned_data.get("warranty_reason")

        if customer and vehicle and vehicle.customer_id != customer.pk:
            self.add_error(
                "vehicle",
                "O veículo selecionado não pertence ao cliente informado.",
            )

        if order_type in ["warranty", "return"]:
            if not warranty_origin_order:
                self.add_error(
                    "warranty_origin_order",
                    "Informe a OS original para garantia ou retorno.",
                )

            if not warranty_reason:
                self.add_error(
                    "warranty_reason",
                    "Informe o motivo da garantia ou retorno.",
                )

        return cleaned_data


class ServiceOrderCreateForm(ServiceOrderForm):
    class Meta(ServiceOrderForm.Meta):
        fields = [
            "customer",
            "vehicle",
            "assigned_mechanic",
            "priority",
            "title",
            "description",
            "status",
            "order_type",
            "warranty_origin_order",
            "warranty_reason",
        ]


class ServiceOrderTechnicalForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = [
            "diagnosis",
            "solution",
            "status",
        ]

        widgets = {
            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o diagnóstico técnico",
                    "rows": 5,
                }
            ),
            "solution": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o serviço executado",
                    "rows": 5,
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

        labels = {
            "diagnosis": "Diagnóstico técnico",
            "solution": "Serviço executado",
            "status": "Status",
        }


class ServiceOrderItemForm(forms.ModelForm):
    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=money_widget("Ex: R$ 100,00"),
    )

    class Meta:
        model = ServiceOrderItem
        fields = [
            "item_type",
            "description",
            "quantity",
            "unit_price",
        ]

        widgets = {
            "item_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a descrição do item",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a quantidade",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }

        labels = {
            "item_type": "Tipo",
            "description": "Descrição",
            "quantity": "Quantidade",
        }


class ServiceOrderNoteForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderNote
        fields = [
            "note_type",
            "text",
        ]

        widgets = {
            "note_type": forms.Select(attrs={"class": "form-select"}),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite uma observação interna sobre a ordem de serviço",
                    "rows": 4,
                }
            ),
        }

        labels = {
            "note_type": "Tipo da observação",
            "text": "Observação",
        }


class ServiceOrderTimeEntryFinishForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderTimeEntry
        fields = [
            "note",
        ]

        widgets = {
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descreva o que foi feito durante este período de trabalho",
                    "rows": 3,
                }
            ),
        }

        labels = {
            "note": "Observação do apontamento",
        }


class ServiceOrderApprovalForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderApproval
        fields = [
            "channel",
            "notes",
        ]

        widgets = {
            "channel": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Ex: Cliente aprovou o orçamento por WhatsApp às 14h30.",
                }
            ),
        }

        labels = {
            "channel": "Canal de aprovação",
            "notes": "Observações da aprovação",
        }
