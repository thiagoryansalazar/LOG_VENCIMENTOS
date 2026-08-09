from django.contrib import admin
from django.urls import include, path, re_path

from .views import spa_index


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("src.routes.urls")),
    re_path(r"^(?!api/|admin/|static/).*$", spa_index, name="spa-index"),
]
