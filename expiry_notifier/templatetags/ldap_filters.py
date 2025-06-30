from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def filetime_to_date(value):
    if not value or str(value) in ("0", "9223372036854775807"):
        return None
    try:
        value = int(value)
        return datetime(1601, 1, 1) + timedelta(microseconds=value // 10)
    except (ValueError, TypeError):
        return None