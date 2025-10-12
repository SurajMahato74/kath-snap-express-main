from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

def react_app_view(request, path=''):
    try:
        with open(os.path.join(settings.BASE_DIR, 'dist', 'index.html'), 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("index.html not found", status=404)

def ngrok_bypass_view(request):
    # Simple bypass for ngrok warning
    response = HttpResponse("Ngrok bypass successful")
    response['ngrok-skip-browser-warning'] = 'any'
    return response

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("accounts.api_urls")),  # Include API URLs with api/ prefix
    path("ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),
    path("", include("accounts.api_urls")),  # Include API URLs at root level for backward compatibility
]

# Static files (MUST come before catch-all)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all for React routes (MUST be last)
urlpatterns += [re_path(r'^.*$', react_app_view, name='react_app')]