from decimal import Decimal, InvalidOperation

from django import forms


class BRLDecimalField(forms.DecimalField):
    """
    DecimalField that accepts Brazilian currency format.

    Accepted examples:
    - R$ 1.234,56
    - 1.234,56
    - 1234,56
    - 1234.56
    """

    default_error_messages = {
        "invalid": "Informe um valor monetário válido. Exemplo: R$ 150,00.",
    }

    def to_python(self, value):
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


def money_widget(placeholder="Ex: R$ 150,00"):
    return forms.TextInput(
        attrs={
            "class": "form-control money-input",
            "placeholder": placeholder,
            "inputmode": "decimal",
            "autocomplete": "off",
        }
    )
