from django.conf import settings
from django.http import FileResponse, Http404


def spa_index(_request):
    index_path = settings.FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        raise Http404("Frontend build nao encontrado. Execute npm run build antes de servir a SPA.")
    return FileResponse(index_path.open("rb"), content_type="text/html")
