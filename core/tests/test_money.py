from decimal import Decimal

import pytest

from core.money import (
    MONEY_ZERO,
    calculate_net_amount,
    ensure_non_negative_money,
    format_brl,
    quantize_money,
    to_decimal,
)


def test_to_decimal_returns_decimal_from_string():
    assert to_decimal("10.50") == Decimal("10.50")


def test_to_decimal_returns_default_for_invalid_value():
    assert to_decimal("invalid") == MONEY_ZERO


def test_quantize_money_uses_two_decimal_places():
    assert quantize_money("10.555") == Decimal("10.56")


def test_ensure_non_negative_money_accepts_zero():
    assert ensure_non_negative_money("0.00") == Decimal("0.00")


def test_ensure_non_negative_money_rejects_negative_value():
    with pytest.raises(ValueError, match="não pode ser negativo"):
        ensure_non_negative_money("-1.00", field_name="valor")


def test_calculate_net_amount_subtracts_discount_once():
    assert calculate_net_amount("100.00", "15.50") == Decimal("84.50")


def test_calculate_net_amount_never_returns_negative_value():
    assert calculate_net_amount("50.00", "100.00") == Decimal("0.00")


def test_calculate_net_amount_rejects_negative_gross_amount():
    with pytest.raises(ValueError, match="valor bruto não pode ser negativo"):
        calculate_net_amount("-10.00", "0.00")


def test_calculate_net_amount_rejects_negative_discount():
    with pytest.raises(ValueError, match="desconto não pode ser negativo"):
        calculate_net_amount("10.00", "-1.00")


def test_format_brl_formats_decimal_value():
    assert format_brl(Decimal("1234.56")) == "R$ 1.234,56"


def test_format_brl_formats_invalid_value_as_zero():
    assert format_brl("invalid") == "R$ 0,00"
