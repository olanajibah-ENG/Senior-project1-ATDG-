
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

print("MAIN URLS.PY LOADED!")



schema_view = get_schema_view(
    openapi.Info(
        title="Code Analysis API",
        default_version='v1',
        description="API for Code Analysis Microservice",
        contact=openapi.Contact(email="contact@ai-project.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def health_check(request):
    """Health check endpoint for Docker healthcheck"""
    return HttpResponse("OK", status=200)

urlpatterns = [
    path('admin/', admin.site.urls),  # استخدام admin العادي
    path('api/analysis/', include('core_ai.urls')), # مسارات API لتطبيق core_ai
    path('health/', health_check, name='health_check'),  # Health check لـ Docker
    path('test/', lambda request: HttpResponse("TEST ENDPOINT WORKS!"), name='test'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)