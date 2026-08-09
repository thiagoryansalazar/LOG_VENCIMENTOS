import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger("atlas.auth")


class AtlasAPIKeyMiddleware:
    """Protege a API com X-API-Key (credential de servico) OU Bearer JWT (operador).

    A chave via header continua valida como credencial de servico para scripts e
    integracoes; o fluxo de negocio da SPA passa a usar autenticacao de usuario
    por Bearer JWT. As rotas de autenticacao e documentacao sao publicas.
    """

    PUBLIC_PATHS = {
        "/health",
        "/health/",
        "/api/docs/",
        "/api/schema/",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
    }

    PROTECTED_PREFIXES = ("/api/",)
    PROTECTED_PATHS = {"/lotes/validar", "/lotes/validar/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def _autenticar_jwt(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False

        token = auth[len("Bearer "):].strip()
        if not token:
            return False

        try:
            access = AccessToken(token)
        except TokenError:
            return False

        user_id = access.get("user_id")
        if user_id is None:
            return False

        User = get_user_model()
        user = User.objects.filter(id=user_id, is_active=True).first()
        if user is None:
            return False

        request.user = user
        request.jwt_authenticated = True
        return True

    def __call__(self, request):
        # A chave de servico e reconhecida em qualquer rota (inclusive as
        # publicas como /auth/me), para que a view saiba o tipo de credencial.
        if request.headers.get("X-API-Key") == settings.ATLAS_API_KEY:
            request.api_key_authenticated = True

        if request.path_info in self.PUBLIC_PATHS:
            return self.get_response(request)

        if request.path_info.startswith("/admin/"):
            return self.get_response(request)

        if not self._deve_proteger(request.path_info):
            return self.get_response(request)

        # O preflight CORS e sempre anonimo: o navegador nao envia headers
        # customizados como X-API-Key no OPTIONS. Exigir credencial aqui faria
        # todo pedido cross-origin falhar antes da requisicao real.
        if request.method == "OPTIONS":
            return self.get_response(request)

        if getattr(request, "api_key_authenticated", False):
            return self.get_response(request)

        if self._autenticar_jwt(request):
            return self.get_response(request)

        if request.headers.get("Authorization"):
            return JsonResponse(
                {"erro": "Token de acesso invalido ou expirado."},
                status=401,
            )

        return JsonResponse(
            {"erro": "API Key ausente ou invalida."},
            status=401,
        )

    def _deve_proteger(self, path_info):
        return path_info in self.PROTECTED_PATHS or path_info.startswith(self.PROTECTED_PREFIXES)
