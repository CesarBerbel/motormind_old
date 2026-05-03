import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


def only_digits(value):
    """
    Remove non-numeric characters.
    """
    return re.sub(r"\D", "", value or "")


def validate_cpf(value):
    """
    Validate Brazilian CPF.
    """
    cpf = only_digits(value)

    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")

    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")

    total = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit

    if digit != int(cpf[9]):
        raise ValidationError("CPF inválido.")

    total = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit

    if digit != int(cpf[10]):
        raise ValidationError("CPF inválido.")


def validate_cnpj(value):
    """
    Validate Brazilian CNPJ.
    """
    cnpj = only_digits(value)

    if len(cnpj) != 14:
        raise ValidationError("CNPJ deve conter 14 dígitos.")

    if cnpj == cnpj[0] * 14:
        raise ValidationError("CNPJ inválido.")

    def calculate_digit(document, weights):
        total = sum(int(document[i]) * weights[i] for i in range(len(weights)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_1 = calculate_digit(cnpj, weights_1)

    if digit_1 != int(cnpj[12]):
        raise ValidationError("CNPJ inválido.")

    weights_2 = [6] + weights_1
    digit_2 = calculate_digit(cnpj, weights_2)

    if digit_2 != int(cnpj[13]):
        raise ValidationError("CNPJ inválido.")


def validate_document(value):
    """
    Validate CPF or CNPJ automatically.
    """
    document = only_digits(value)

    if not document:
        return

    if len(document) == 11:
        validate_cpf(document)
        return

    if len(document) == 14:
        validate_cnpj(document)
        return

    raise ValidationError("Documento deve ser CPF ou CNPJ válido.")


def validate_positive_decimal(value):
    """
    Validate that a Decimal value is greater than zero.
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("Informe um número válido.")

    if decimal_value <= Decimal("0.00"):
        raise ValidationError("O valor deve ser maior que zero.")


def validate_non_negative_decimal(value):
    """
    Validate that a Decimal value is zero or positive.
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("Informe um número válido.")

    if decimal_value < Decimal("0.00"):
        raise ValidationError("O valor não pode ser negativo.")


def validate_reason_min_length(value, min_length=5):
    """
    Validate minimum length for operational reasons/justifications.
    """
    text = (value or "").strip()

    if len(text) < min_length:
        raise ValidationError(
            f"O motivo deve conter pelo menos {min_length} caracteres."
        )
