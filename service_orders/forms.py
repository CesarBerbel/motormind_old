from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from customers.models import Vehicle

from .models import ServiceOrder, ServiceOrderItem, ServiceOrderNote, ServiceOrderTimeEntry


class BRLDecimalField(forms.DecimalField):
    """
    Field that accepts Brazilian money formats.
    """

    default_error_messages = {
        "invalid": "Informe um valor monetário válido. Exemplo: R$ 150,00.",
    }

    def to_python(self, value):
        """
        Convert Brazilian money string to Decimal.
        """
        if value in self.empty_values:
            return None

        if isinstance(value, Decimal):
            return value

        value = str(value).strip()
        value = value.replace("R$", "")
        value = value.replace(" ", "")

        if "," in value:
            value = value.replace(".", "")
            value = value.replace(",", ".")

        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise forms.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
            ) from exc


class ServiceOrderForm(forms.ModelForm):
    """
    Form used by administrators and attendants to create and update service orders.
    """

    labor_cost = BRLDecimalField(
        label="Valor da mão de obra",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control money-input",
                "placeholder": "Ex: R$ 150,00",
                "inputmode": "decimal",
                "autocomplete": "off",
            }
        ),
    )

    parts_cost = BRLDecimalField(
        label="Valor das peças",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control money-input",
                "placeholder": "Ex: R$ 200,00",
                "inputmode": "decimal",
                "autocomplete": "off",
            }
        ),
    )

    discount = BRLDecimalField(
        label="Desconto",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0.00"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control money-input",
                "placeholder": "Ex: R$ 50,00",
                "inputmode": "decimal",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = ServiceOrder
        fields = [
            "customer",
            "vehicle",
            "assigned_mechanic",
            "title",
            "description",
            "diagnosis",
            "solution",
            "status",
            "labor_cost",
            "parts_cost",
            "discount",
            "expected_delivery_date",
        ]

        widgets = {
            "customer": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_customer",
                }
            ),
            "vehicle": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_vehicle",
                }
            ),
            "assigned_mechanic": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
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
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "expected_delivery_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
            ),
        }

        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo",
            "assigned_mechanic": "Mecânico responsável",
            "title": "Título",
            "description": "Descrição do problema",
            "diagnosis": "Diagnóstico técnico",
            "solution": "Serviço executado",
            "status": "Status",
            "expected_delivery_date": "Previsão de entrega",
        }

    def __init__(self, *args, **kwargs):
        """
        Limit vehicle options according to selected customer and mechanic group.
        """
        super().__init__(*args, **kwargs)

        self.fields["vehicle"].queryset = Vehicle.objects.none()

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
        self.fields[
            "assigned_mechanic"
        ].empty_label = "Selecione o mecânico responsável"

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
        """
        Return zero when labor cost is empty.
        """
        return self.cleaned_data.get("labor_cost") or Decimal("0.00")

    def clean_parts_cost(self):
        """
        Return zero when parts cost is empty.
        """
        return self.cleaned_data.get("parts_cost") or Decimal("0.00")

    def clean_discount(self):
        """
        Return zero when discount is empty.
        """
        return self.cleaned_data.get("discount") or Decimal("0.00")

    def clean(self):
        """
        Validate if vehicle belongs to selected customer.
        """
        cleaned_data = super().clean()

        customer = cleaned_data.get("customer")
        vehicle = cleaned_data.get("vehicle")

        if customer and vehicle and vehicle.customer != customer:
            raise forms.ValidationError(
                "O veículo selecionado não pertence ao cliente informado."
            )

        return cleaned_data


class ServiceOrderTechnicalForm(forms.ModelForm):
    """
    Form used by mechanics to update technical fields only.
    """

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
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

        labels = {
            "diagnosis": "Diagnóstico técnico",
            "solution": "Serviço executado",
            "status": "Status",
        }


class ServiceOrderItemForm(forms.ModelForm):
    """
    Form used to create and update service order items.
    """

    unit_price = BRLDecimalField(
        label="Preço unitário",
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput(
            attrs={
                "class": "form-control money-input",
                "placeholder": "Ex: R$ 100,00",
                "inputmode": "decimal",
                "autocomplete": "off",
            }
        ),
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
            "item_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
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
    """
    Form used to create internal service order notes.
    """

    class Meta:
        model = ServiceOrderNote
        fields = [
            "note_type",
            "text",
        ]

        widgets = {
            "note_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
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
    """
    Form used to finish a mechanic time entry.
    """

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