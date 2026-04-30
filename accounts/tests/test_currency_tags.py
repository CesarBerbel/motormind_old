from decimal import Decimal

from accounts.templatetags.currency import brl


def test_brl_formats_decimal_value():
    """
    Test if Decimal value is formatted as Brazilian Real.
    """
    assert brl(Decimal("1234.56")) == "R$ 1.234,56"


def test_brl_formats_integer_value():
    """
    Test if integer value is formatted as Brazilian Real.
    """
    assert brl(1000) == "R$ 1.000,00"


def test_brl_formats_string_decimal_value():
    """
    Test if string decimal value is formatted as Brazilian Real.
    """
    assert brl("99.90") == "R$ 99,90"


def test_brl_returns_zero_for_invalid_value():
    """
    Test if invalid value returns zero currency.
    """
    assert brl("invalid-value") == "R$ 0,00"


def test_brl_returns_zero_for_none():
    """
    Test if None returns zero currency.
    """
    assert brl(None) == "R$ 0,00"
