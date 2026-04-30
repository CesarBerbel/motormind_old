from django import forms

from .models import ServiceOrder


class ServiceOrderForm(forms.ModelForm):
    """
    Form used by administrators and attendants to create and update service orders.
    """

    class Meta:
        model = ServiceOrder
        fields = [
            "customer",
            "vehicle",
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
                }
            ),
            "vehicle": forms.Select(
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
            "labor_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "parts_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "discount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "expected_delivery_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

        labels = {
            "customer": "Cliente",
            "vehicle": "Veículo",
            "title": "Título",
            "description": "Descrição do problema",
            "diagnosis": "Diagnóstico técnico",
            "solution": "Serviço executado",
            "status": "Status",
            "labor_cost": "Valor da mão de obra",
            "parts_cost": "Valor das peças",
            "discount": "Desconto",
            "expected_delivery_date": "Previsão de entrega",
        }

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
