import re

from django import forms
from django.core.exceptions import ValidationError
from validate_docbr import CNPJ, CPF

from .models import Customer, Vehicle


class CustomerForm(forms.ModelForm):
    """
    Form used to create and update customers with strict validation.
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
                    "placeholder": "(00) 00000-0000",
                    "id": "phone_mask",  # Hook for future JS mask
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
                    "placeholder": "000.000.000-00",
                    "id": "cpf_mask",  # Hook for future JS mask
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
            "document": "CPF",
            "address": "Endereço",
            "notes": "Observações",
            "is_active": "Cliente ativo",
        }

    def clean_document(self):
        document = self.cleaned_data.get("document")
        if not document:
            return document

        digits = re.sub(r"\D", "", document)

        # Lógica para CPF (11 dígitos)
        if len(digits) == 11:
            validator = CPF()
            if not validator.validate(digits):
                raise ValidationError("CPF inválido.")

        # Lógica para CNPJ (14 dígitos)
        elif len(digits) == 14:
            validator = CNPJ()
            if not validator.validate(digits):
                raise ValidationError("CNPJ inválido.")

        else:
            raise ValidationError("O documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos.")

        # Verificação de duplicidade
        query = Customer.objects.filter(document=digits)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise ValidationError(
                "Este documento já está cadastrado para outro cliente."
            )

        return digits

    def clean_email(self):
        """
        Normalize email to lowercase and check uniqueness.
        """
        email = self.cleaned_data.get("email")
        if not email:
            return email

        email = email.strip().lower()

        # Uniqueness check
        query = Customer.objects.filter(email=email)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise ValidationError("Este e-mail já está em uso por outro cliente.")

        return email

    def clean_phone(self):
        """
        Validate Brazilian phone format (DDD + number).
        """
        phone = self.cleaned_data.get("phone")
        if not phone:
            return phone

        # Remove non-digit characters
        phone_digits = re.sub(r"\D", "", phone)

        # Brazilian numbers have 10 (fixed) or 11 (mobile) digits
        if len(phone_digits) < 10 or len(phone_digits) > 11:
            raise ValidationError(
                "O telefone deve ter entre 10 e 11 dígitos (incluindo o DDD)."
            )

        return phone_digits


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
