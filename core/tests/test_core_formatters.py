from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

from core.templatetags.core_formatters import brl, date_br, datetime_br


def test_brl_template_filter_formats_decimal_value():
    assert brl(Decimal("1234.56")) == "R$ 1.234,56"


def test_brl_template_filter_formats_none_as_zero():
    assert brl(None) == "R$ 0,00"


def test_date_br_template_filter_formats_date():
    assert date_br(date(2026, 5, 3)) == "03/05/2026"


def test_date_br_template_filter_returns_empty_string_for_none():
    assert date_br(None) == ""


def test_datetime_br_template_filter_formats_datetime(settings):
    settings.TIME_ZONE = "America/Sao_Paulo"

    value = timezone.make_aware(datetime(2026, 5, 3, 14, 30))

    assert datetime_br(value) == "03/05/2026 14:30"


def test_datetime_br_template_filter_returns_empty_string_for_none():
    assert datetime_br(None) == ""
