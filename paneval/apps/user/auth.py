"""Authorization."""
from typing import Optional

from django.contrib.auth.backends import BaseBackend

from .models import User


class UsernamePasswordBackend(BaseBackend):
    """Authenticate via username + password."""

    def authenticate(
            self,
            request,
            username: Optional[str] = None,
            password: Optional[str] = None,
    ) -> Optional[User]:
        """Authenticate by matching username then checking password."""
        if not username or not password:
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if not user.check_password(password):
            return None
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by pk."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SMSCodeBackend(BaseBackend):
    """Backend."""

    def authenticate(
            self,
            request,
            country_code: str,
            phone: str,
            code: str,
    ) -> Optional[User]:
        """Authenticate."""
        return User.objects.get(phone=phone, country_code=country_code)

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by pk."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def has_perm(self, user: User, perm, obj=None) -> bool:
        """Return true if status is approved."""
        return user.status == "Approved"
