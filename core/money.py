from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONEY_ZERO = Decimal("0.00")
MONEY_QUANT = Decimal("0.01")


def to_decimal(value, default=MONEY_ZERO):
    """
    Convert a value to Decimal safely.

    Never use float for financial calculations. If a float is received, it is
    converted through str(value) to reduce binary floating point issues.
    """
    if value is None or value == "":
        return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def quantize_money(value):
    """
    Normalize monetary values to two decimal places.
    """
    return to_decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def ensure_non_negative_money(value, field_name="valor"):
    """
    Validate that a monetary value is not negative.
    """
    decimal_value = quantize_money(value)

    if decimal_value < MONEY_ZERO:
        raise ValueError(f"O campo {field_name} não pode ser negativo.")

    return decimal_value


def calculate_net_amount(gross_amount, discount_amount):
    """
    Calculate net amount using the MotorMind standard rule.

    net_total = max(gross_total - discount, 0)
    """
    gross = quantize_money(gross_amount)
    discount = quantize_money(discount_amount)

    if gross < MONEY_ZERO:
        raise ValueError("O valor bruto não pode ser negativo.")

    if discount < MONEY_ZERO:
        raise ValueError("O desconto não pode ser negativo.")

    net = gross - discount

    if net < MONEY_ZERO:
        return MONEY_ZERO

    return quantize_money(net)


def format_brl(value):
    """
    Format Decimal-compatible value as Brazilian Real.
    """
    decimal_value = quantize_money(value)
    formatted_value = f"{decimal_value:,.2f}"
    formatted_value = (
        formatted_value.replace(",", "X").replace(".", ",").replace("X", ".")
    )

    return f"R$ {formatted_value}"
