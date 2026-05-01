import re

from django.core.exceptions import ValidationError


def only_digits(value):
    """
    Remove non-numeric characters.
    """
    return re.sub(r"\D", "", value or "")


# =========================
# CPF VALIDATION
# =========================


def validate_cpf(value):
    """
    Validate Brazilian CPF.
    """
    cpf = only_digits(value)

    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")

    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")

    # First digit
    total = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit

    if digit != int(cpf[9]):
        raise ValidationError("CPF inválido.")

    # Second digit
    total = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit = (total * 10) % 11
    digit = 0 if digit == 10 else digit

    if digit != int(cpf[10]):
        raise ValidationError("CPF inválido.")


# =========================
# CNPJ VALIDATION
# =========================


def validate_cnpj(value):
    """
    Validate Brazilian CNPJ.
    """
    cnpj = only_digits(value)

    if len(cnpj) != 14:
        raise ValidationError("CNPJ deve conter 14 dígitos.")

    if cnpj == cnpj[0] * 14:
        raise ValidationError("CNPJ inválido.")

    def calculate_digit(cnpj, weights):
        total = sum(int(cnpj[i]) * weights[i] for i in range(len(weights)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    # First digit
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_1 = calculate_digit(cnpj, weights_1)

    if digit_1 != int(cnpj[12]):
        raise ValidationError("CNPJ inválido.")

    # Second digit
    weights_2 = [6] + weights_1
    digit_2 = calculate_digit(cnpj, weights_2)

    if digit_2 != int(cnpj[13]):
        raise ValidationError("CNPJ inválido.")


# =========================
# GENERIC DOCUMENT VALIDATOR
# =========================


def validate_document(value):
    """
    Validate CPF or CNPJ automatically.
    """
    document = only_digits(value)

    if len(document) == 11:
        validate_cpf(document)
    elif len(document) == 14:
        validate_cnpj(document)
    else:
        raise ValidationError("Documento deve ser CPF ou CNPJ válido.")
