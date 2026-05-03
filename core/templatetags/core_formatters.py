from django import template

from core.dates import format_date_br, format_datetime_br
from core.money import format_brl

register = template.Library()


@register.filter(name="brl")
def brl(value):
    """
    Format a value as Brazilian Real.
    """
    return format_brl(value)


@register.filter(name="date_br")
def date_br(value):
    """
    Format a date as dd/mm/yyyy.
    """
    return format_date_br(value)


@register.filter(name="datetime_br")
def datetime_br(value):
    """
    Format a datetime as dd/mm/yyyy HH:MM.
    """
    return format_datetime_br(value)
