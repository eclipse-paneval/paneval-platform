"""Caches."""
from typing import Optional

from django.core.cache import cache


def save_sms_code(country_code: str, phone: str, code: str):
    """Save SMS code to cache."""
    cache.set(_sms_code_key(country_code, phone), code, timeout=60*10)


def get_sms_code(country_code: str, phone: str) -> Optional[str]:
    """Retrieve cached SMS code."""
    return cache.get(_sms_code_key(country_code, phone))


def del_sms_code(country_code: str, phone: str):
    """Delete cached SMS code."""
    return cache.delete(_sms_code_key(country_code, phone))


def _sms_code_key(country_code: str, phone: str) -> str:
    return f'smscode:{country_code}:{phone}'
