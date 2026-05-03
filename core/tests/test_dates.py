from datetime import date, datetime

from django.utils import timezone

from core.dates import (
    format_date_br,
    format_datetime_br,
    is_past_date,
    local_now,
    local_today,
)


def test_local_today_returns_date():
    assert isinstance(local_today(), date)


def test_local_now_returns_timezone_aware_datetime():
    value = local_now()

    assert timezone.is_aware(value)


def test_is_past_date_returns_true_for_past_date():
    yesterday = local_today() - timezone.timedelta(days=1)

    assert is_past_date(yesterday) is True


def test_is_past_date_returns_false_for_today():
    assert is_past_date(local_today()) is False


def test_is_past_date_returns_false_for_none():
    assert is_past_date(None) is False


def test_format_date_br_returns_empty_string_for_none():
    assert format_date_br(None) == ""


def test_format_date_br_formats_date():
    assert format_date_br(date(2026, 5, 3)) == "03/05/2026"


def test_format_datetime_br_returns_empty_string_for_none():
    assert format_datetime_br(None) == ""


def test_format_datetime_br_formats_datetime(settings):
    settings.TIME_ZONE = "America/Sao_Paulo"

    value = timezone.make_aware(datetime(2026, 5, 3, 14, 30))

    assert format_datetime_br(value) == "03/05/2026 14:30"
