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
    # Serve React index.html from public_html root
    try:
        with open('/home/ezeywayc/public_html/index.html', 'r') as f:
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

def api_root_view(request):
    return HttpResponse("Django API Root - Working!", content_type='text/plain')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("accounts.api_urls")),  # API with /api/ prefix for React
    path("api", api_root_view, name='api_root'),  # Handle /api without trailing slash
    path("ngrok-bypass/", ngrok_bypass_view, name='ngrok_bypass'),
    # Serve React frontend for root URL only
    re_path(r'^$', react_frontend_view, name='react_frontend'),
    # Catch-all for React SPA routing (must be last)
    re_path(r'^(?!admin/|accounts/|api|ngrok-bypass/).*$', react_frontend_view, name='react_spa'),
]

# Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Add this at the end of urlpatterns
urlpatterns += static('/media/', document_root=settings.MEDIA_ROOT)


