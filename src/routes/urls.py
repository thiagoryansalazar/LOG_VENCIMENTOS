from django.urls import path

from .views import health, validar_lote_view


urlpatterns = [
    path("health", health, name="health"),
    path("lotes/validar", validar_lote_view, name="validar-lote"),
]
