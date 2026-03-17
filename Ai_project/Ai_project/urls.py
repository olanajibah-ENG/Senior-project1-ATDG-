"""
Ai_project/urls.py - Main URL Configuration
============================================
مسؤولية هذا الملف: توزيع الطلبات على التطبيقات فقط.
لا يحتوي على أي مسار داخلي لـ core_ai — هذه مسؤولية core_ai/urls.py.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from core_ai.views.folder_upload import FolderUploadView

print("MAIN URLS.PY LOADED!")

# ── Swagger schema ────────────────────────────────────────────────────────────
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

# ── Utility views (مسؤولية المشروع الرئيسي) ──────────────────────────────────

def health_check(request):
    """Health check endpoint for Docker healthcheck"""
    return HttpResponse("OK", status=200)

def api_root(request):
    """API root endpoint"""
    if request.method == 'GET':
        user_email = request.GET.get('user_email', '')
        return JsonResponse({
            'message': 'API Root - Available endpoints',
            'endpoints': [
                '/codefiles/',
                '/analysis-results/',
                '/analyze/',
                '/task-status/',
                '/admin/',
                '/health/',
            ],
            'user_email': user_email if user_email else None,
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ── URL patterns ──────────────────────────────────────────────────────────────
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # ✅ كل مسارات core_ai مفوّضة لملفها الخاص
    path('', include('core_ai.urls')),

    # Utility endpoints (مسؤولية المشروع الرئيسي)
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health_check'),
    path('test/', lambda request: HttpResponse("TEST ENDPOINT WORKS!"), name='test'),

    # Swagger / ReDoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/',   schema_view.with_ui('redoc',   cache_timeout=0), name='schema-redoc'),
    path('folder-upload/', FolderUploadView.as_view(), name='folder-upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)