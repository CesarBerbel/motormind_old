import pytest
from django.core.exceptions import ValidationError

from core.validators import (
    only_digits,
    validate_cnpj,
    validate_cpf,
    validate_document,
    validate_non_negative_decimal,
    validate_positive_decimal,
    validate_reason_min_length,
)


def test_only_digits_removes_non_numeric_characters():
    assert only_digits("(11) 99999-8888") == "11999998888"


def test_validate_cpf_accepts_valid_cpf():
    validate_cpf("529.982.247-25")


def test_validate_cpf_rejects_invalid_cpf():
    with pytest.raises(ValidationError):
        validate_cpf("111.111.111-11")


def test_validate_cnpj_accepts_valid_cnpj():
    validate_cnpj("04.252.011/0001-10")


def test_validate_cnpj_rejects_invalid_cnpj():
    with pytest.raises(ValidationError):
        validate_cnpj("11.111.111/1111-11")


def test_validate_document_accepts_valid_cpf():
    validate_document("529.982.247-25")


def test_validate_document_accepts_valid_cnpj():
    validate_document("04.252.011/0001-10")


def test_validate_document_rejects_invalid_length():
    with pytest.raises(ValidationError):
        validate_document("123")


def test_validate_positive_decimal_accepts_positive_value():
    validate_positive_decimal("10.00")


def test_validate_positive_decimal_rejects_zero():
    with pytest.raises(ValidationError):
        validate_positive_decimal("0.00")


def test_validate_positive_decimal_rejects_negative_value():
    with pytest.raises(ValidationError):
        validate_positive_decimal("-1.00")


def test_validate_non_negative_decimal_accepts_zero():
    validate_non_negative_decimal("0.00")


def test_validate_non_negative_decimal_rejects_negative_value():
    with pytest.raises(ValidationError):
        validate_non_negative_decimal("-0.01")


def test_validate_reason_min_length_accepts_valid_reason():
    validate_reason_min_length("Ajuste operacional")


def test_validate_reason_min_length_rejects_short_reason():
    with pytest.raises(ValidationError):
        validate_reason_min_length("abc")
