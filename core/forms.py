from django import forms

from .models import CompanySettings


class CompanySettingsForm(forms.ModelForm):
    """
    Form used in the administrative area to maintain official workshop data.
    """

    class Meta:
        model = CompanySettings
        fields = [
            "name",
            "legal_name",
            "document",
            "state_registration",
            "municipal_registration",
            "phone",
            "whatsapp",
            "email",
            "website",
            "address_line",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "opening_hours",
            "service_terms",
            "is_configured",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control"}),
            "document": forms.TextInput(attrs={"class": "form-control", "placeholder": "CPF ou CNPJ"}),
            "state_registration": forms.TextInput(attrs={"class": "form-control"}),
            "municipal_registration": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "address_line": forms.TextInput(attrs={"class": "form-control"}),
            "number": forms.TextInput(attrs={"class": "form-control"}),
            "complement": forms.TextInput(attrs={"class": "form-control"}),
            "neighborhood": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control", "maxlength": "2"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "opening_hours": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "service_terms": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "is_configured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
