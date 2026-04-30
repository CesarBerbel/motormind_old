from django import forms

from customers.models import Vehicle

from .models import ServiceOrder, ServiceOrderItem


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
                    "id": "id_customer",
                }
            ),
            "vehicle": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_vehicle",
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
                    "placeholder": "Ex: 150,00",
                    "step": "0.01",
                }
            ),
            "parts_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: 200,00",
                    "step": "0.01",
                }
            ),
            "discount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: 50,00",
                    "step": "0.01",
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

    def __init__(self, *args, **kwargs):
        """
        Limit vehicle options according to selected customer when possible.
        """
        super().__init__(*args, **kwargs)

        self.fields["vehicle"].queryset = Vehicle.objects.none()

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
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: 100,00",
                    "step": "0.01",
                    "min": "0.00",
                }
            ),
        }

        labels = {
            "item_type": "Tipo",
            "description": "Descrição",
            "quantity": "Quantidade",
            "unit_price": "Preço unitário",
        }
