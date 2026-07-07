from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from . import oidc
from .models import User, UserSocialAccount


OIDC_SETTINGS = {
    "OIDC_ENABLED": "",
    "OIDC_ISSUER_URL": "https://issuer.example",
    "OIDC_CLIENT_ID": "paneval-client",
    "OIDC_CLIENT_SECRET": "secret",
    "OIDC_SCOPES": "openid email profile",
    "OIDC_REDIRECT_PATH": "/api/users/sso",
    "OIDC_REDIRECT_URI": "",
    "OIDC_SUCCESS_REDIRECT": "https://paneval.example/",
    "WEBSITE_URL": "https://paneval.example",
}


class OIDCTests(TestCase):
    """OpenID Connect login flow tests."""

    @override_settings(
        OIDC_ENABLED="",
        OIDC_ISSUER_URL="",
        OIDC_CLIENT_ID="",
        OIDC_CLIENT_SECRET="",
    )
    def test_oidc_status_disabled_without_config(self):
        response = self.client.get("/api/users/oidc/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"enabled": False})

    @override_settings(**OIDC_SETTINGS)
    @patch("paneval.apps.user.views.oidc.new_nonce", return_value="nonce-value")
    @patch("paneval.apps.user.views.oidc.new_state", return_value="state-value")
    @patch("paneval.apps.user.views.oidc.discover")
    def test_oidc_login_redirects_to_provider(
            self,
            discover,
            _new_state,
            _new_nonce,
    ):
        client = oidc.create_client(oidc.load_config())
        client.authorization_endpoint = "https://issuer.example/auth"
        discover.return_value = client

        response = self.client.get("/api/users/oidc/login")

        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response["Location"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "issuer.example")
        self.assertEqual(parsed.path, "/auth")
        query = parse_qs(parsed.query)
        self.assertEqual(query["client_id"], ["paneval-client"])
        self.assertEqual(
            query["redirect_uri"],
            ["https://paneval.example/api/users/sso"],
        )
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["openid email profile"])
        self.assertEqual(query["state"], ["state-value"])
        self.assertEqual(query["nonce"], ["nonce-value"])
        self.assertEqual(
            self.client.session[oidc.SESSION_REDIRECT_URI_KEY],
            "https://paneval.example/api/users/sso",
        )

    @override_settings(**OIDC_SETTINGS)
    @patch("paneval.apps.user.views.oidc.exchange_code_for_claims")
    @patch("paneval.apps.user.views.oidc.discover")
    def test_oidc_callback_creates_approved_user(
            self,
            discover,
            exchange_code_for_claims,
    ):
        issuer = "https://issuer.example"
        self._set_oidc_session()
        discover.return_value = SimpleNamespace(provider_info={"issuer": issuer})
        exchange_code_for_claims.return_value = {
            "sub": "subject-1",
            "iss": issuer,
            "aud": "paneval-client",
            "exp": 9999999999,
            "iat": 1,
            "nonce": "nonce-value",
            "email": "User@Example.com",
            "name": "OIDC User",
        }

        response = self.client.get(
            "/api/users/sso",
            {"code": "auth-code", "state": "state-value"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://paneval.example/")

        user = User.objects.get()
        self.assertEqual(user.status, User.Status.APPROVED)
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.name, "OIDC User")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

        oidc_account = UserSocialAccount.objects.get(
            social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
        )
        self.assertEqual(oidc_account.user_id, user.pk)
        self.assertEqual(oidc_account.social_open_id, f"{issuer}|subject-1")
        self.assertEqual(oidc_account.extras["issuer"], issuer)
        self.assertEqual(oidc_account.extras["subject"], "subject-1")

        email_account = UserSocialAccount.objects.get(
            social_platform=UserSocialAccount.SocialPlat.EMAIL,
        )
        self.assertEqual(email_account.user_id, user.pk)
        self.assertEqual(email_account.social_open_id, "user@example.com")

    @override_settings(**OIDC_SETTINGS)
    @patch("paneval.apps.user.views.oidc.exchange_code_for_claims")
    @patch("paneval.apps.user.views.oidc.discover")
    def test_oidc_callback_reuses_linked_user(
            self,
            discover,
            exchange_code_for_claims,
    ):
        issuer = "https://issuer.example"
        user = User.objects.create_user(
            username="existing",
            country_code="+86",
            phone="13800000000",
            status=User.Status.APPROVED,
        )
        UserSocialAccount.objects.create(
            user_id=user.pk,
            social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
            social_open_id=f"{issuer}|subject-1",
            created_at=timezone.now(),
        )
        self._set_oidc_session()
        discover.return_value = SimpleNamespace(provider_info={"issuer": issuer})
        exchange_code_for_claims.return_value = {
            "sub": "subject-1",
            "iss": issuer,
            "aud": "paneval-client",
            "exp": 9999999999,
            "iat": 1,
            "nonce": "nonce-value",
        }

        response = self.client.get(
            "/api/users/sso",
            {"code": "auth-code", "state": "state-value"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(
            UserSocialAccount.objects.filter(
                social_platform=UserSocialAccount.SocialPlat.OPENID_CONNECT,
            ).count(),
            1,
        )
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    @override_settings(**OIDC_SETTINGS)
    def test_oidc_callback_rejects_invalid_state(self):
        self._set_oidc_session()

        response = self.client.get(
            "/api/users/sso",
            {"code": "auth-code", "state": "wrong-state"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "OIDC state is invalid."})

    def _set_oidc_session(self):
        session = self.client.session
        session[oidc.SESSION_STATE_KEY] = "state-value"
        session[oidc.SESSION_NONCE_KEY] = "nonce-value"
        session[oidc.SESSION_REDIRECT_URI_KEY] = (
            "https://paneval.example/api/users/sso"
        )
        session.save()
