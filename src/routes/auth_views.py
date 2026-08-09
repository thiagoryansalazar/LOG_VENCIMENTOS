import logging

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import (
    LoginSerializer,
    LogoutSerializer,
    MeResponseSerializer,
    RefreshResponseSerializer,
    RefreshSerializer,
    TokenResponseSerializer,
    UsuarioSerializer,
)

logger = logging.getLogger("atlas.auth")


class LoginThrottle(AnonRateThrottle):
    """Rate limit por IP para a rota de login (anti brute-force)."""

    scope = "login"


@extend_schema(
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        401: TokenResponseSerializer,
    },
)
@api_view(["POST"])
@throttle_classes([LoginThrottle])
def login_view(request: Request) -> Response:
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ip = get_ident(request)
    username = serializer.validated_data["username"]
    user = authenticate(
        request,
        username=username,
        password=serializer.validated_data["password"],
    )
    if user is None:
        logger.warning("login_falhou ip=%s usuario=%s", ip, username)
        return Response(
            {"erro": "Credenciais invalidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)
    logger.info("login_ok ip=%s usuario=%s", ip, user.username)
    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UsuarioSerializer(user).data,
        }
    )


@extend_schema(
    request=RefreshSerializer,
    responses={
        200: RefreshResponseSerializer,
        401: RefreshResponseSerializer,
    },
)
@api_view(["POST"])
def refresh_view(request: Request) -> Response:
    serializer = RefreshSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        refresh = RefreshToken(serializer.validated_data["refresh"])
    except TokenError:
        return Response(
            {"erro": "Refresh token invalido ou expirado."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response({"access": str(refresh.access_token)})


@extend_schema(
    request=LogoutSerializer,
    responses={
        205: None,
        400: None,
    },
)
@api_view(["POST"])
def logout_view(request: Request) -> Response:
    serializer = LogoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        refresh = RefreshToken(serializer.validated_data["refresh"])
        refresh.blacklist()
    except TokenError:
        return Response(
            {"erro": "Refresh token invalido ou ja revogado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    logger.info("logout_ok")
    return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(
    responses={
        200: MeResponseSerializer,
        401: MeResponseSerializer,
    },
)
@api_view(["GET"])
def me_view(request: Request) -> Response:
    if request.user.is_authenticated:
        return Response(
            {
                "autenticado": True,
                "tipo": "usuario",
                "usuario": UsuarioSerializer(request.user).data,
            }
        )

    if getattr(request, "api_key_authenticated", False):
        return Response(
            {
                "autenticado": True,
                "tipo": "api_key",
                "usuario": None,
            }
        )

    return Response(
        {"autenticado": False, "tipo": None, "usuario": None},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def get_ident(request: Request) -> str:
    """IP do cliente para auditoria, respeitando proxy reverso se configurado."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "desconhecido")
