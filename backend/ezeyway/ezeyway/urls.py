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

def serve_react_static(request):
    # Serve React static files
    import mimetypes
    from django.http import FileResponse, Http404
    import os
    
    # Get the full path from the request
    path = request.path.lstrip('/')
    file_path = f'/home/ezeywayc/public_html/ezeyway/dist/{path}'
    
    # Check if file exists
    if not os.path.exists(file_path):
        # If it's not a static file, serve React index.html for SPA routing
        return react_frontend_view(request)
    
    try:
        content_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    except Exception as e:
        raise Http404(f"Error serving file: {e}")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("accounts.api_urls")),  # API at root since Passenger uses /api base
    path("ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),
    # React frontend for root
    re_path(r'^$', react_frontend_view, name='react_frontend'),
    # Serve all other files as React static files
    re_path(r'^.*$', serve_react_static, name='react_static'),
]

# Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)