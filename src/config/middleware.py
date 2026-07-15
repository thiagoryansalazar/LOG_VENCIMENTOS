from django.conf import settings
from django.http import JsonResponse


class AtlasAPIKeyMiddleware:
    """Protege a API com uma chave simples no header X-API-Key."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info in {"/health", "/health/"}:
            return self.get_response(request)

        if request.path_info.startswith("/admin/"):
            return self.get_response(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.ATLAS_API_KEY:
            return JsonResponse(
                {"erro": "API Key ausente ou invalida."},
                status=401,
            )

        return self.get_response(request)
