from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def landing_view(request):
    return render(request, "index.html")

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

# Add catch-all for React routes (must be last)
urlpatterns += [path('', landing_view, name='landing')]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/', document_root=settings.BASE_DIR / "dist")
