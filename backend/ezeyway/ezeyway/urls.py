from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
import os

# ---------------------------
# Helper views
# ---------------------------

def ngrok_bypass_view(request):
    """Ngrok bypass for development/testing"""
    response = HttpResponse("Ngrok bypass successful")
    response['ngrok-skip-browser-warning'] = 'any'
    return response

def api_root(request):
    """Return a simple message or JSON for the API root"""
    return JsonResponse({
        "message": "Welcome to Ezeyway Django API",
        "endpoints": [
            "/login/",
            "/register/",
            "/categories/"
        ]
    })

def react_frontend_view(request):
    """Serve React frontend index.html for non-API routes"""
    try:
        with open('/home/ezeywayc/public_html/index.html', 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React app not found", status=404)

def serve_react_static(request):
    """Serve React static assets"""
    import mimetypes
    from django.http import FileResponse, Http404
    path = request.path.lstrip('/')
    file_path = f'/home/ezeywayc/public_html/ezeyway/dist/{path}'
    if not os.path.exists(file_path):
        return react_frontend_view(request)
    try:
        content_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    except Exception as e:
        raise Http404(f"Error serving file: {e}")

# ---------------------------
# URL patterns
# ---------------------------

urlpatterns = [
    # ---------------------------
    # API ROOT
    # ---------------------------
    path("api/", api_root, name="api_root"),

    # ---------------------------
    # Django Admin under /api/admin/
    # ---------------------------
    path("api/admin/", admin.site.urls),

    # ---------------------------
    # Django accounts API
    # ---------------------------
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("accounts.api_urls")),

    # ---------------------------
    # Ngrok bypass (if needed)
    # ---------------------------
    path("api/ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),

    # ---------------------------
    # React frontend root
    # ---------------------------
    re_path(r'^$', react_frontend_view, name='react_frontend'),

    # ---------------------------
    # React SPA catch-all (exclude API/admin)
    # ---------------------------
    re_path(r'^(?!api/|admin/|accounts/|ngrok-bypass/).*$', react_frontend_view, name='react_spa'),
]

# ---------------------------
# Static files
# ---------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Extra media path (redundant but safe)
urlpatterns += static('/media/', document_root=settings.MEDIA_ROOT)
