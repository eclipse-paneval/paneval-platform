"""Define endpoints."""

from django.urls import path
from . import views

urlpatterns = [
    path("login", views.Login.as_view()),
    path("oidc/status", views.OIDCStatus.as_view()),
    path("oidc/login", views.OIDCLogin.as_view()),
    path("sso", views.OIDCCallback.as_view()),
    path("me", views.Me.as_view()),
]
