from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

def ngrok_bypass_view(request):
    # Simple bypass for ngrok warning
    response = HttpResponse("Ngrok bypass successful")
    response['ngrok-skip-browser-warning'] = 'any'
    return response

def react_frontend_view(request):
    # Serve React index.html
    try:
        with open('/home/ezeywayc/public_html/ezeyway/dist/index.html', 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React app not found", status=404)

def serve_react_static(request, path):
    # Serve React static files
    import mimetypes
    from django.http import FileResponse, Http404
    
    file_path = f'/home/ezeywayc/public_html/ezeyway/dist/{path}'
    try:
        content_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    except FileNotFoundError:
        raise Http404("File not found")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("accounts.api_urls")),  # API at root since Passenger uses /api base
    path("ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),
    # Serve React static files
    re_path(r'^(assets|images|.*\.(js|css|svg|png|jpg|ico|mp3))$', serve_react_static, name='react_static'),
    # React frontend fallback for root
    re_path(r'^$', react_frontend_view, name='react_frontend'),
]

# Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)