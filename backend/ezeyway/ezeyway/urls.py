from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
import os

# ---------------------------
# Helper views
# ---------------------------

def api_root(request):
    return JsonResponse({
        "message": "Welcome to Ezeyway Django API",
        "endpoints": ["/login/", "/register/", "/categories/"]
    })

def react_frontend_view(request):
    """Serve React SPA index.html"""
    try:
        with open('/home/ezeywayc/public_html/index.html', 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React app not found", status=404)

# ---------------------------
# URL patterns
# ---------------------------
urlpatterns = [
    # Django API
    path('', api_root, name='api_root'),  # root path now
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    # path('superadmin/', include('superadmin.urls')),  # commented out to prevent errors
    path('vendor-profiles/', include('vendor_profiles.urls')),

    # React SPA root
    re_path(r'^$', react_frontend_view, name='react_frontend'),

    # React SPA catch-all (exclude media/static/admin subpaths)
    re_path(r'^(?!admin/|media/|static/).*$', react_frontend_view, name='react_spa'),
]

# ---------------------------
# Static and media files
# ---------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static('/media/', document_root=settings.MEDIA_ROOT)
