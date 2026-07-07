"""Serializers."""
from typing_extensions import Required
from rest_framework import serializers

from paneval import validators
from .models import User, UserSocialAccount, UserTask


class SMSCodeSerializer(
        serializers.Serializer, validators.PhoneValidatorMixin,
):
    """Send SMS code for registration."""

    is_login = serializers.BooleanField(required=False)
    country_code = serializers.CharField(required=False, default='+86')
    phone = serializers.CharField(required=True)
    poll_data = serializers.DictField(required=False)


class RegistrationSerializer(
        serializers.Serializer, validators.PhoneValidatorMixin,
):
    """Registration for users."""

    email = serializers.EmailField(required=True)
    country_code = serializers.CharField(required=False, default='+86')
    phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    poll_data = serializers.DictField(required=False)


class AuthorizationSerializer(
        serializers.Serializer, validators.PhoneValidatorMixin,
):
    """Authorization for users."""

    country_code = serializers.CharField(required=False, default='+86')
    phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    """User."""

    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    created_at = serializers.DateTimeField(required=False)
    tasks = serializers.ListField(required=False)


    class Meta:
        """Meta."""

        model = User

        fields = [
            "id", "username", "country_code", "phone", "name", "status",
            "organization", "email",
            "organization_en",
            "is_staff", "is_researcher",
            "created_at", "tasks", "updated_at",
            "is_private_model","eva_length", "available_mark_count",
            "huggingface",
        ]

    def get_email(self, obj):
        item = UserSocialAccount.objects.filter(
            user_id=obj.id,
            social_platform=UserSocialAccount.SocialPlat.EMAIL,
        ).first()

        if item is None:
            return None

        return item.social_open_id

    def get_username(self, obj):
        item = UserSocialAccount.objects.filter(
            user_id=obj.id,
            social_platform=UserSocialAccount.SocialPlat.USERNAME,
        ).first()

        if item is None:
            return None

        return item.social_open_id


def replace_asterisk(s: str) -> str:
    l = len(s)
    if l == 1:
        return '*'
    if l == 2:
        return s[0] + '*'
    if l == 3:
        return s[0] + '*' + s[-1]

    rl = int(l / 2)
    rl = rl if rl < 4 else 4
    left = int((l - rl) / 2)
    right = l - rl - left
    return s[:left] + ('*' * rl) + s[-right:]



class ComplementSerializer(serializers.Serializer):
    """Serializer to complete user information."""

    username = serializers.RegexField(
        r'^[a-z][a-z0-9]+$',
        required=True,
        min_length=3,
        max_length=32,
    )
    name = serializers.CharField(required=True)
    organization = serializers.CharField(required=True)
    organization_en = serializers.CharField(required=True)
    tasks = serializers.ListField(
        child=serializers.ChoiceField(choices=UserTask.Sence.choices)
    )


class RevisalSerializer(serializers.Serializer):
    """Update user's status."""

    status = serializers.ChoiceField(choices=User.Status.choices, required=False)  # noqa
    is_staff = serializers.BooleanField(required=False)
    is_researcher = serializers.BooleanField(required=False)
    eva_length = serializers.IntegerField(required=False)
    available_mark_count = serializers.IntegerField(required=False)


class ComplementMeSerializer(serializers.Serializer):
    """Serializer to complete my information."""
    organization_en = serializers.CharField(required=True)


class LoginSerializer(serializers.Serializer):
    """Login with username and password."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
