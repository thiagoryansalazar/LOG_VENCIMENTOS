import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger("atlas.auth")


class SecurityHeadersMiddleware:
    """Cabecalhos de seguranca para o HTML da SPA.

    A defesa central e a Content-Security-Policy. Os tokens JWT vivem em
    localStorage, que e legivel por qualquer script executando na origem: se um
    XSS conseguir injetar script, ele rouba a sessao. A CSP corta justamente o
    vetor de entrada ao proibir script de origem externa e script inline, que
    sao a forma usual de um payload de XSS executar.

    `frame-ancestors 'none'` impede clickjacking (o app embutido em iframe de
    terceiros). A politica nao se aplica a `/api/docs/`, cuja UI depende de
    script inline proprio do Swagger.
    """

    ROTAS_SEM_CSP = ("/api/docs/", "/api/schema/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path_info.startswith(self.ROTAS_SEM_CSP):
            return response

        response.setdefault("Content-Security-Policy", self._politica())
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        return response

    def _politica(self) -> str:
        # `connect-src` precisa cobrir a origem do dev server (Vite em :5173),
        # que chama a API a partir de outra porta. Em producao a SPA e servida
        # pelo proprio Django, entao 'self' basta.
        connect = ["'self'", *settings.CORS_ALLOWED_ORIGINS] if settings.DEBUG else ["'self'"]

        diretivas = [
            "default-src 'self'",
            # Sem 'unsafe-inline' e sem 'unsafe-eval': e o que efetivamente
            # bloqueia a execucao de um payload de XSS injetado no DOM.
            "script-src 'self'",
            # Componentes React/Recharts aplicam estilo via atributo inline;
            # 'unsafe-inline' aqui nao permite execucao de codigo.
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            f"connect-src {' '.join(connect)}",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        return "; ".join(diretivas)


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
