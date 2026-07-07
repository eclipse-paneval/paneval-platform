"""Views of user."""
import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response as JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .serializers import LoginSerializer, UserSerializer
from . import models, oidc

logger = logging.getLogger(__name__)


class Login(APIView):
    """Login with username and password."""

    def post(self, request, format=None):
        """Authenticate and create session."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return JsonResponse({'detail': 'Invalid username or password.'}, status=401)
        login(request, user)
        return JsonResponse(UserSerializer(user).data, status=200)


class OIDCStatus(APIView):
    """OpenID Connect configuration status."""

    def get(self, request, format=None):
        """Return whether OIDC login is enabled."""
        return JsonResponse({"enabled": oidc.load_config().enabled}, status=200)


class OIDCLogin(APIView):
    """Start OpenID Connect login."""

    def get(self, request, format=None):
        """Redirect the user to the configured OIDC provider."""
        config = oidc.load_config()
        if not config.enabled:
            return JsonResponse(
                {"detail": "OpenID Connect is not configured."},
                status=404,
            )

        try:
            client = oidc.discover(config)
            state = oidc.new_state()
            nonce = oidc.new_nonce()
            redirect_uri = oidc.callback_redirect_uri(config)
            request.session[oidc.SESSION_STATE_KEY] = state
            request.session[oidc.SESSION_NONCE_KEY] = nonce
            request.session[oidc.SESSION_REDIRECT_URI_KEY] = redirect_uri
            request.session.modified = True
            authorization_url = oidc.build_authorization_url(
                config,
                client,
                state,
                nonce,
                redirect_uri,
            )
        except oidc.OIDCError as exc:
            logger.warning("Unable to start OIDC login: %s", exc)
            return JsonResponse({"detail": str(exc)}, status=400)

        return HttpResponseRedirect(authorization_url)


class OIDCCallback(APIView):
    """Complete OpenID Connect login."""

    def get(self, request, format=None):
        """Validate the provider callback and create a Django session."""
        config = oidc.load_config()
        if not config.enabled:
            return JsonResponse(
                {"detail": "OpenID Connect is not configured."},
                status=404,
            )

        provider_error = request.GET.get("error")
        if provider_error:
            detail = request.GET.get("error_description") or provider_error
            return JsonResponse({"detail": detail}, status=400)

        code = request.GET.get("code")
        state = request.GET.get("state")
        expected_state = request.session.pop(oidc.SESSION_STATE_KEY, None)
        nonce = request.session.pop(oidc.SESSION_NONCE_KEY, None)
        redirect_uri = request.session.pop(
            oidc.SESSION_REDIRECT_URI_KEY,
            oidc.callback_redirect_uri(config),
        )
        request.session.modified = True

        if not code or not state or not expected_state or state != expected_state:
            return JsonResponse({"detail": "OIDC state is invalid."}, status=400)
        if not nonce:
            return JsonResponse({"detail": "OIDC nonce is missing."}, status=400)

        try:
            client = oidc.discover(config)
            claims = oidc.exchange_code_for_claims(
                client,
                request.META.get("QUERY_STRING", ""),
                state,
                nonce,
                redirect_uri,
            )
            user = oidc.get_or_create_user(
                claims,
                client.provider_info.get("issuer") or config.issuer_url,
            )
            login(request, user, backend=oidc.LOGIN_BACKEND)
        except oidc.OIDCError as exc:
            logger.warning("Unable to complete OIDC login: %s", exc)
            return JsonResponse({"detail": str(exc)}, status=400)

        return HttpResponseRedirect(config.success_redirect)


class Me(APIView):
    """Current logined user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """Fetch the current user's information."""
        social_accounts = models.UserSocialAccount.objects.filter(
            user_id=request.user.pk,
        )
        extra_fields = {}
        for item in social_accounts:
            extra_fields[item.to_field()] = item.social_open_id
        serializer = UserSerializer(request.user)
        return JsonResponse(serializer.data, status=200)

    def delete(self, request, format=None):
        """Logout."""
        logout(request)
        return HttpResponse(status=204)
