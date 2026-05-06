from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import forms

MONEY_QUANT = Decimal("0.01")


def normalize_money_value(value, *, default=None):
    if value in (None, ""):
        return default

    if isinstance(value, Decimal):
        decimal_value = value
    else:
        text = str(value).strip()
        text = text.replace("R$", "")
        text = text.replace(" ", "")

        if "," in text:
            text = text.replace(".", "")
            text = text.replace(",", ".")

        decimal_value = Decimal(text)

    return decimal_value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def normalize_quantity_value(value, *, default=None):
    if value in (None, ""):
        return default

    if isinstance(value, Decimal):
        decimal_value = value
    else:
        text = str(value).strip().replace(",", ".")
        decimal_value = Decimal(text)

    return decimal_value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


class BRLDecimalField(forms.DecimalField):
    default_error_messages = {
        "invalid": "Informe um valor monetário válido. Exemplo: R$ 150,00.",
        "max_digits": "Informe um valor com no máximo %(max)s dígitos.",
        "max_decimal_places": "Informe um valor com no máximo %(max)s casas decimais.",
        "max_whole_digits": "Informe um valor com no máximo %(max)s dígitos antes da vírgula.",
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("decimal_places", 2)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None

        try:
            return normalize_money_value(value)
        except (InvalidOperation, ValueError) as exc:
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
            "step": "0.01",
        }
    )
