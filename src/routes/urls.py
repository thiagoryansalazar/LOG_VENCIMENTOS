from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    disparar_alerta_manual_view,
    health,
    listar_lotes_criticos_view,
    listar_lotes_view,
    validar_lote_view,
)


urlpatterns = [
    path("health", health, name="health"),
    path("lotes/validar", validar_lote_view, name="validar-lote"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="api-docs",
    ),
    path("api/v1/lotes/validar", validar_lote_view, name="api-v1-validar-lote"),
    path("api/v1/lotes", listar_lotes_view, name="api-v1-listar-lotes"),
    path(
        "api/v1/lotes/criticos",
        listar_lotes_criticos_view,
        name="api-v1-lotes-criticos",
    ),
    path(
        "api/v1/alertas/disparar",
        disparar_alerta_manual_view,
        name="api-v1-disparar-alerta",
    ),
]
