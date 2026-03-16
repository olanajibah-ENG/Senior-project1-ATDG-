from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

def health_check(request):
    """Health check endpoint for Docker healthcheck"""
    return HttpResponse("OK", status=200)

schema_view = get_schema_view(
    openapi.Info(
        title="UPM API",
        default_version='v1',
        description="University Project Management System API",
        contact=openapi.Contact(email="contact@upm.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Health check for Docker
    path('health/', health_check, name='health_check'),

    # API Routes - كل مسارات UPM تحت بادئة موحدة
    path('api/upm/', include('core_upm.urls')),
    # JWT Authentication - عام لجميع التطبيقات
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)