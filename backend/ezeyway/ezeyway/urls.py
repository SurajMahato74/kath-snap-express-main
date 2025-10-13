from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
import os

def ngrok_bypass_view(request):
    # Simple bypass for ngrok warning
    response = HttpResponse("Ngrok bypass successful")
    response['ngrok-skip-browser-warning'] = 'any'
    return response

def react_fallback_view(request):
    # Serve React index.html from public_html
    try:
        with open('/home/ezeywayc/public_html/index.html', 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React app not found", status=404)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("accounts.api_urls")),
    path("ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),
    # React fallback for all other routes
    re_path(r'^.*$', react_fallback_view, name='react_fallback'),
]

# Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)