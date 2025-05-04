from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from api.views import FrontendAppView

# Endpoint para probar CORS
def cors_test_view(request):
    return JsonResponse({"ok": True})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/cors-test/', cors_test_view),
    
    # Sirve el index.html para cualquier ruta no API (SPA)
    re_path(r'^.*$', FrontendAppView.as_view(), name='frontend'),
]

# Solo en desarrollo: sirve archivos estáticos desde STATIC_ROOT
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
