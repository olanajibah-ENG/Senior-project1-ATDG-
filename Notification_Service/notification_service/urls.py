"""
URL configuration for notification_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# إعداد التوثيق التلقائي للـ API
schema_view = get_schema_view(
    openapi.Info(
        title="Notification Service API",
        default_version='v1',
        description="API لخدمة الإشعارات - AutoTest & DocGen",
        terms_of_service="https://www.autotest-docgen.com/policies/terms/",
        contact=openapi.Contact(email="contact@autotest-docgen.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # API endpoints
    path('', include('notifications.urls')),

    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Health check endpoint
    path('health/', lambda request: JsonResponse({'status': 'healthy', 'service': 'notification-service'}), name='health-check'),
]

# استيراد JsonResponse للـ health check
from django.http import JsonResponse
