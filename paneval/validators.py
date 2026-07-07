"""Validators."""
import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PhoneValidatorMixin:
    """Mixin class to validate phone number."""

    PHONE_REGEX = re.compile(r'^1\d{10}$')

    def validate_phone(self, value: str) -> str:
        """Throw an error if value is not a phone number."""
        if not self.PHONE_REGEX.match(value):
            raise serializers.ValidationError(_("Phone number is invalid."))
        return value
