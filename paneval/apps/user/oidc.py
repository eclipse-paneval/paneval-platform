"""OpenID Connect support."""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from oic.exception import PyoidcError
from oic.oic import Client
from oic.oic.message import AuthorizationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.utils.settings import OicClientSettings

from .models import User, UserSocialAccount


SESSION_NONCE_KEY = "oidc_nonce"
SESSION_REDIRECT_URI_KEY = "oidc_redirect_uri"
SESSION_STATE_KEY = "oidc_state"

LOGIN_BACKEND = "paneval.apps.user.auth.UsernamePasswordBackend"

_DEFAULT_SCOPES = ["openid", "email", "profile"]
_FALSE_VALUES = {"0", "false", "no", "off"}
_TRUE_VALUES = {"1", "true", "yes", "on"}


class OIDCError(Exception):
    """Raised when OIDC processing fails."""


@dataclass(frozen=True)
class OIDCConfig:
    """Runtime OIDC configuration."""

    enabled: bool
    issuer_url: str
    client_id: str
    client_secret: str
    scopes: List[str]
    redirect_path: str
    success_redirect: str
    timeout: float


def load_config() -> OIDCConfig:
    """Load OIDC settings after local_settings overrides have been applied."""
    issuer_url = str(getattr(settings, "OIDC_ISSUER_URL", "") or "").rstrip("/")
    client_id = str(getattr(settings, "OIDC_CLIENT_ID", "") or "")
    client_secret = str(getattr(settings, "OIDC_CLIENT_SECRET", "") or "")
    enabled_value = _optional_bool(getattr(settings, "OIDC_ENABLED", None))
    configured = bool(issuer_url and client_id and client_secret)
    enabled = configured if enabled_value is None else configured and enabled_value

    return OIDCConfig(
        enabled=enabled,
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
        scopes=_parse_scopes(getattr(settings, "OIDC_SCOPES", _DEFAULT_SCOPES)),
        redirect_path=str(
            getattr(settings, "OIDC_REDIRECT_PATH", "/api/users/sso")
            or "/api/users/sso"
        ),
        success_redirect=str(
            getattr(settings, "OIDC_SUCCESS_REDIRECT", "")
            or getattr(settings, "WEBSITE_URL", "/")
            or "/"
        ),
        timeout=_timeout(getattr(settings, "OIDC_HTTP_TIMEOUT", 5.0)),
    )


def callback_redirect_uri(config: OIDCConfig) -> str:
    """Return the public callback URI sent to the OIDC provider."""
    configured_uri = str(getattr(settings, "OIDC_REDIRECT_URI", "") or "")
    if configured_uri:
        return configured_uri

    website_url = str(getattr(settings, "WEBSITE_URL", "") or "").rstrip("/")
    redirect_path = "/" + config.redirect_path.lstrip("/")
    if not website_url:
        return redirect_path
    return f"{website_url}{redirect_path}"


def new_state() -> str:
    """Generate a state value for an OIDC authorization request."""
    return secrets.token_urlsafe(32)


def new_nonce() -> str:
    """Generate a nonce value for ID token replay protection."""
    return secrets.token_urlsafe(32)


def create_client(config: OIDCConfig) -> Client:
    """Create a pyoidc client for the configured provider."""
    client = Client(
        client_id=config.client_id,
        client_authn_method=CLIENT_AUTHN_METHOD,
        settings=OicClientSettings(timeout=config.timeout),
    )
    client.client_secret = config.client_secret
    return client


def discover(config: OIDCConfig) -> Client:
    """Fetch provider metadata and keys into a pyoidc client."""
    if not config.enabled:
        raise OIDCError("OpenID Connect is not configured.")

    client = create_client(config)
    try:
        client.provider_config(config.issuer_url)
    except Exception as exc:
        raise OIDCError("OIDC provider discovery failed.") from exc
    return client


def build_authorization_url(
        config: OIDCConfig,
        client: Client,
        state: str,
        nonce: str,
        redirect_uri: str,
) -> str:
    """Build the provider authorization URL with pyoidc."""
    try:
        url, _, _, _ = client.authorization_request_info(request_args={
            "client_id": config.client_id,
            "nonce": nonce,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config.scopes,
            "state": state,
        })
    except PyoidcError as exc:
        raise OIDCError("OIDC authorization request could not be built.") from exc
    return url


def exchange_code_for_claims(
        client: Client,
        callback_query: str,
        state: str,
        nonce: str,
        redirect_uri: str,
) -> Dict[str, Any]:
    """Parse the callback and exchange the code using pyoidc."""
    try:
        client.parse_response(
            AuthorizationResponse,
            info=callback_query,
            sformat="urlencoded",
            state=state,
        )

        client.state2nonce[state] = nonce
        token_response = client.do_access_token_request(
            state=state,
            request_args={"redirect_uri": redirect_uri},
            authn_method=_token_authn_method(client),
            nonce=nonce,
        )
    except Exception as exc:
        raise OIDCError("OIDC authorization code exchange failed.") from exc

    claims = _claims_from_token_response(token_response)
    if claims.get("nonce") != nonce:
        raise OIDCError("OIDC ID token nonce is invalid.")
    return claims


def get_or_create_user(claims: Dict[str, Any], issuer: str) -> User:
    """Find or auto-create the local user for OIDC claims."""
    subject = str(claims.get("sub") or "")
    if not subject:
        raise OIDCError("OIDC ID token is missing subject.")

    social_open_id = _oidc_social_open_id(issuer, subject)
    now = timezone.now()
    extras = _account_extras(claims, issuer, subject)
    email = _claim_email(claims)

    with transaction.atomic():
        account = UserSocialAccount.objects.select_for_update().filter(
            social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
            social_open_id=social_open_id,
        ).first()
        if account is not None:
            account.extras = extras
            account.updated_at = now
            account.save(update_fields=["extras", "updated_at"])
            return User.objects.get(pk=account.user_id)

        user = _find_user_by_email_account(email)
        if user is None:
            user = _create_approved_user(claims, issuer, subject, email)
        elif UserSocialAccount.objects.filter(
                user_id=user.pk,
                social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
        ).exists():
            raise OIDCError("User is already linked to another OIDC identity.")

        UserSocialAccount.objects.create(
            user_id=user.pk,
            social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
            social_open_id=social_open_id,
            extras=extras,
            created_at=now,
            updated_at=now,
        )
        _ensure_email_account(user, email, now)

    return user


def _optional_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None


def _parse_scopes(value: Any) -> List[str]:
    if value is None:
        return list(_DEFAULT_SCOPES)
    if isinstance(value, str):
        scopes = value.replace(",", " ").split()
    else:
        scopes = [str(item) for item in value]

    if "openid" not in scopes:
        scopes.insert(0, "openid")
    return scopes


def _timeout(value: Any) -> float:
    try:
        return float(value or 5.0)
    except (TypeError, ValueError):
        return 5.0


def _token_authn_method(client: Client) -> str:
    methods = client.provider_info.get(
        "token_endpoint_auth_methods_supported",
        ["client_secret_basic"],
    )
    for method in ("client_secret_basic", "client_secret_post"):
        if method in methods:
            return method
    raise OIDCError("OIDC token endpoint authentication method is unsupported.")


def _claims_from_token_response(token_response: Any) -> Dict[str, Any]:
    id_token = token_response.get("id_token")
    if id_token is None:
        raise OIDCError("OIDC token response is missing ID token.")
    if hasattr(id_token, "to_dict"):
        return id_token.to_dict()
    if isinstance(id_token, dict):
        return id_token
    raise OIDCError("OIDC ID token claims are unavailable.")


def _oidc_social_open_id(issuer: str, subject: str) -> str:
    value = f"{issuer}|{subject}"
    max_length = UserSocialAccount._meta.get_field("social_open_id").max_length
    if len(value) <= max_length:
        return value
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _account_extras(
        claims: Dict[str, Any],
        issuer: str,
        subject: str,
) -> Dict[str, Any]:
    skipped = {"at_hash", "aud", "auth_time", "c_hash", "exp", "iat", "iss", "sub"}
    extras = {
        key: value
        for key, value in claims.items()
        if key not in skipped and _is_json_value(value)
    }
    extras["issuer"] = issuer
    extras["subject"] = subject
    return extras


def _is_json_value(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def _claim_email(claims: Dict[str, Any]) -> Optional[str]:
    if claims.get("email_verified") is False:
        return None
    email = str(claims.get("email") or "").strip().lower()
    if not email:
        return None
    return email


def _find_user_by_email_account(email: Optional[str]) -> Optional[User]:
    if not email:
        return None
    account = UserSocialAccount.objects.filter(
        social_platform=UserSocialAccount.SocialPlat.EMAIL,
        social_open_id=email,
    ).first()
    if account is None:
        return None
    return User.objects.filter(pk=account.user_id).first()


def _create_approved_user(
        claims: Dict[str, Any],
        issuer: str,
        subject: str,
        email: Optional[str],
) -> User:
    digest = hashlib.sha256(f"{issuer}|{subject}".encode("utf-8")).hexdigest()
    user = User(
        country_code="OC",
        email=email or "",
        name=_display_name(claims, email),
        phone=digest[:20],
        status=User.Status.APPROVED,
        username=f"oidc_{digest[:32]}",
    )
    user.set_unusable_password()
    user.save()
    return user


def _display_name(claims: Dict[str, Any], email: Optional[str]) -> str:
    value = (
        claims.get("name")
        or claims.get("preferred_username")
        or (email.split("@", 1)[0] if email else "")
        or "OpenID Connect User"
    )
    return str(value)[:40]


def _ensure_email_account(
        user: User,
        email: Optional[str],
        now,
) -> None:
    if not email:
        return
    UserSocialAccount.objects.get_or_create(
        social_platform=UserSocialAccount.SocialPlat.EMAIL,
        social_open_id=email,
        defaults={
            "user_id": user.pk,
            "created_at": now,
            "updated_at": now,
        },
    )
