from django.utils import timezone


def local_today():
    """
    Return the current date using Django's active timezone.
    """
    return timezone.localdate()


def local_now():
    """
    Return the current datetime using Django's timezone utilities.
    """
    return timezone.now()


def is_past_date(value):
    """
    Check whether a date is before today in the local timezone.
    """
    if value is None:
        return False

    return value < local_today()


def format_date_br(value):
    """
    Format date as dd/mm/yyyy.
    """
    if not value:
        return ""

    return value.strftime("%d/%m/%Y")


def format_datetime_br(value):
    """
    Format datetime as dd/mm/yyyy HH:MM.
    """
    if not value:
        return ""

    local_value = timezone.localtime(value)

    return local_value.strftime("%d/%m/%Y %H:%M")
