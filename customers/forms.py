from django import forms

from .models import Customer, Vehicle


class CustomerForm(forms.ModelForm):
    """
    Form used to create and update customers.
    """

    class Meta:
        model = Customer
        fields = [
            "name",
            "phone",
            "email",
            "document",
            "address",
            "notes",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o nome completo do cliente",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o telefone do cliente",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o email do cliente",
                }
            ),
            "document": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o documento fiscal",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o endereço do cliente",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite observações importantes sobre o cliente",
                    "rows": 4,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

        labels = {
            "name": "Nome",
            "phone": "Telefone",
            "email": "Email",
            "document": "Documento",
            "address": "Endereço",
            "notes": "Observações",
            "is_active": "Cliente ativo",
        }


class VehicleForm(forms.ModelForm):
    """
    Form used to create and update vehicles.
    """

    class Meta:
        model = Vehicle
        fields = [
            "customer",
            "plate",
            "brand",
            "model",
            "year",
            "color",
            "chassis_number",
            "mileage",
            "notes",
            "is_active",
        ]

        widgets = {
            "customer": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "plate": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a matrícula ou placa",
                }
            ),
            "brand": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a marca do veículo",
                }
            ),
            "model": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o modelo do veículo",
                }
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o ano do veículo",
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a cor do veículo",
                }
            ),
            "chassis_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite o número do chassi",
                }
            ),
            "mileage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite a quilometragem atual",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite observações importantes sobre o veículo",
                    "rows": 4,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

        labels = {
            "customer": "Cliente",
            "plate": "Matrícula/Placa",
            "brand": "Marca",
            "model": "Modelo",
            "year": "Ano",
            "color": "Cor",
            "chassis_number": "Número do chassi",
            "mileage": "Quilometragem",
            "notes": "Observações",
            "is_active": "Veículo ativo",
        }

    def clean_plate(self):
        """
        Normalize vehicle plate.
        """
        plate = self.cleaned_data.get("plate")

        if plate:
            return plate.upper().strip()

        return plate
