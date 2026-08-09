from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .auth_views import (
    login_view,
    logout_view,
    me_view,
    refresh_view,
)
from .views import (
    cadastrar_lote_view,
    config_sistema_view,
    consultar_lote_por_id_view,
    disparar_alerta_manual_view,
    health,
    importar_lotes_view,
    atualizar_lote_view,
    listar_historico_alteracoes_view,
    listar_historico_lote_view,
    listar_lotes_criticos_view,
    listar_lotes_view,
    validar_lote_view,
)


urlpatterns = [
    path("health", health, name="health"),
    path("lotes/validar", validar_lote_view, name="validar-lote"),
    path("api/v1/auth/login", login_view, name="api-v1-auth-login"),
    path("api/v1/auth/refresh", refresh_view, name="api-v1-auth-refresh"),
    path("api/v1/auth/logout", logout_view, name="api-v1-auth-logout"),
    path("api/v1/auth/me", me_view, name="api-v1-auth-me"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="api-docs",
    ),
    path("api/v1/config", config_sistema_view, name="api-v1-config-sistema"),
    path("api/v1/lotes/validar", validar_lote_view, name="api-v1-validar-lote"),
    path("api/v1/lotes", listar_lotes_view, name="api-v1-listar-lotes"),
    path(
        "api/v1/lotes/cadastrar",
        cadastrar_lote_view,
        name="api-v1-cadastrar-lote",
    ),
    path(
        "api/v1/lotes/importar",
        importar_lotes_view,
        name="api-v1-importar-lotes",
    ),
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
    path(
        "api/v1/lotes/<int:id>",
        consultar_lote_por_id_view,
        name="api-v1-consultar-lote",
    ),
    path(
        "api/v1/lotes/<int:id>/editar",
        atualizar_lote_view,
        name="api-v1-atualizar-lote",
    ),
    path(
        "api/v1/lotes/<int:id>/historico",
        listar_historico_lote_view,
        name="api-v1-historico-lote",
    ),
    path(
        "api/v1/historico-alteracoes",
        listar_historico_alteracoes_view,
        name="api-v1-historico-alteracoes",
    ),
]
