# 🔗 دليل التكامل - Notification Service

## نظرة عامة
هذا الدليل يوضح كيفية تكامل خدمة الإشعارات مع أنظمة AutoTest & DocGen الأخرى.

## 🏗️ البنية العامة

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UPM_Project   │    │ Notification    │    │   Ai_Project    │
│                 │◄──►│   Service      │◄──►│                 │
│ - Projects      │    │                 │    │ - AI Analysis   │
│ - Users         │    │ - Emails        │    │ - PDF Export    │
│ - Management    │    │ - Queue         │    │ - Code Analysis │
└─────────────────┘    │ - Database      │    └─────────────────┘
                       └─────────────────┘
```

## 📡 نقاط التكامل

### 1. UPM_Project Integration

#### أحداث تحتاج إشعارات
- إنشاء مشروع جديد
- حذف مشروع
- إضافة مستخدم للمشروع
- تغيير حالة المشروع

#### ملفات تحتاج تعديل
```
UPM_Project/core_upm/views/projects.py
UPM_Project/core_upm/views/users.py
UPM_Project/core_upm/models.py
```

#### مثال على التكامل
```python
# في UPM_Project/core_upm/views/projects.py

import requests
from django.conf import settings

NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://notification-service:8000')

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        project = serializer.save()

        # إرسال إشعار للمستخدم
        try:
            requests.post(
                f'{NOTIFICATION_SERVICE_URL}/api/notifications/project/',
                json={
                    'user_email': self.request.user.email,
                    'action': 'created',
                    'project_name': project.name,
                    'project_id': str(project.id),
                    'user_name': self.request.user.get_full_name()
                },
                timeout=3
            )
        except requests.RequestException:
            # لا تتوقف العملية إذا فشل الإشعار
            pass

    def perform_destroy(self, instance):
        project_name = instance.name
        project_id = str(instance.id)

        # إرسال إشعار قبل الحذف
        try:
            requests.post(
                f'{NOTIFICATION_SERVICE_URL}/api/notifications/project/',
                json={
                    'user_email': self.request.user.email,
                    'action': 'deleted',
                    'project_name': project_name,
                    'project_id': project_id,
                    'user_name': self.request.user.get_full_name()
                },
                timeout=3
            )
        except requests.RequestException:
            pass

        instance.delete()
```

### 2. Ai_Project Integration

#### أحداث تحتاج إشعارات
- انتهاء تحليل الكود
- تصدير ملف PDF
- فشل في تحليل الكود
- اكتمال مهمة AI

#### ملفات تحتاج تعديل
```
Ai_project/core_ai/views/export_views.py
Ai_project/core_ai/tasks.py
Ai_project/core_ai/views/analysis.py
```

#### مثال على التكامل
```python
# في Ai_project/core_ai/views/export_views.py

import requests
from django.conf import settings

NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://notification-service:8000')

def export_pdf_with_diagram(request, explanation_id):
    # كود التصدير الحالي...

    try:
        # إرسال إشعار نجاح التصدير
        requests.post(
            f'{NOTIFICATION_SERVICE_URL}/api/notifications/documentation/',
            json={
                'user_email': request.user.email,
                'file_name': f'technical_report_{explanation_id}.pdf',
                'file_type': 'PDF',
                'project_name': 'AI Code Analysis',
                'user_name': request.user.get_full_name()
            },
            timeout=3
        )
    except requests.RequestException:
        pass

    return response
```

## ⚙️ إعدادات Django

### إضافة في UPM_Project/settings.py
```python
# Notification Service Integration
NOTIFICATION_SERVICE_URL = 'http://notification-service:8000'
NOTIFICATION_ENABLED = True
```

### إضافة في Ai_Project/settings.py
```python
# Notification Service Integration
NOTIFICATION_SERVICE_URL = 'http://notification-service:8000'
NOTIFICATION_ENABLED = True
```

## 🐳 Docker Compose Integration

### تعديل docker-compose.yml الرئيسي
```yaml
# في Kamar_11_2025/docker-compose.yml

services:
  # إضافة خدمة الإشعارات
  notification-service:
    image: notification-service:latest
    container_name: notification-service
    ports:
      - "8004:8000"
    environment:
      - NOTIFICATION_SERVICE_URL=http://notification-service:8000
    depends_on:
      - notification_db
    networks:
      - upm_network

  notification-db:
    image: postgres:15
    container_name: notification-db
    environment:
      POSTGRES_DB: notification_service_db
      POSTGRES_USER: notification_user
      POSTGRES_PASSWORD: notification_password
    networks:
      - upm_network

  # تعديل nginx لإضافة routes للإشعارات
  api_gateway:
    # ... existing config ...
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./Notification_Service/nginx/notification.conf:/etc/nginx/conf.d/notification.conf
```

### إعدادات Nginx الجديدة
```nginx
# في Notification_Service/nginx/notification.conf

upstream notification_backend {
    server notification-service:8000;
}

server {
    listen 80;
    server_name notification.yourdomain.com;

    location /api/notifications/ {
        proxy_pass http://notification_backend/api/notifications/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin-notifications/ {
        proxy_pass http://notification_backend/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Middleware للتكامل التلقائي

### إنشاء Middleware في UPM_Project
```python
# UPM_Project/core_upm/middleware.py

import requests
import json
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class NotificationMiddleware(MiddlewareMixin):
    """
    Middleware لإرسال إشعارات تلقائياً
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.notification_url = getattr(settings, 'NOTIFICATION_SERVICE_URL', None)
        self.enabled = getattr(settings, 'NOTIFICATION_ENABLED', True)

    def __call__(self, request):
        response = self.get_response(request)

        # إرسال إشعارات للعمليات المهمة
        if self.enabled and self.notification_url and hasattr(request, 'user') and request.user.is_authenticated:
            self._send_notification_if_needed(request, response)

        return response

    def _send_notification_if_needed(self, request, response):
        """تحديد متى يجب إرسال إشعار"""
        try:
            # مثال: إشعار عند إنشاء مشروع
            if (request.method == 'POST' and
                'projects' in request.path and
                response.status_code == 201):

                data = json.loads(request.body) if request.body else {}
                self._send_project_notification(request.user, 'created', data)

        except Exception as e:
            # لا نريد أن يؤثر فشل الإشعار على التطبيق الرئيسي
            print(f"Notification middleware error: {e}")

    def _send_project_notification(self, user, action, data):
        """إرسال إشعار مشروع"""
        try:
            requests.post(
                f'{self.notification_url}/api/notifications/project/',
                json={
                    'user_email': user.email,
                    'action': action,
                    'project_name': data.get('name', 'Unknown Project'),
                    'user_name': user.get_full_name()
                },
                timeout=2
            )
        except:
            pass
```

## 📊 مراقبة التكامل

### إحصائيات التكامل
```python
# في Notification Service
def integration_stats(request):
    """عرض إحصائيات التكامل مع الأنظمة الأخرى"""
    stats = Notification.objects.aggregate(
        upm_projects=Count('id', filter=Q(related_type='upm_project')),
        ai_exports=Count('id', filter=Q(notification_type='DOCUMENTATION_EXPORTED')),
        total_notifications=Count('id')
    )

    return JsonResponse({
        'integration_stats': stats,
        'systems': {
            'upm_project': 'connected',
            'ai_project': 'connected'
        }
    })
```

## 🔄 معالجة الأخطاء

### Circuit Breaker Pattern
```python
# في settings.py لكل مشروع
NOTIFICATION_CIRCUIT_BREAKER = {
    'failure_threshold': 5,
    'recovery_timeout': 300,  # 5 minutes
    'expected_exception': (requests.RequestException, requests.Timeout)
}

# في utilities.py
class NotificationCircuitBreaker:
    def __init__(self):
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise CircuitBreakerOpenException()

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self):
        # منطق إعادة المحاولة
        pass

    def _on_success(self):
        self.failures = 0
        self.state = 'closed'

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = timezone.now()
        if self.failures >= 5:
            self.state = 'open'
```

## 🧪 اختبار التكامل

### اختبار UPM_Project Integration
```python
# في UPM_Project tests
from unittest.mock import patch

class ProjectNotificationTest(TestCase):
    @patch('requests.post')
    def test_project_creation_notification(self, mock_post):
        # إنشاء مشروع
        response = self.client.post('/api/projects/', {'name': 'Test Project'})

        # التأكد من إرسال الإشعار
        mock_post.assert_called_once_with(
            'http://notification-service:8000/api/notifications/project/',
            json={
                'user_email': 'user@test.com',
                'action': 'created',
                'project_name': 'Test Project',
                'user_name': 'Test User'
            },
            timeout=3
        )
```

### اختبار Ai_Project Integration
```python
# في Ai_Project tests
class ExportNotificationTest(TestCase):
    @patch('requests.post')
    def test_pdf_export_notification(self, mock_post):
        # تصدير PDF
        response = self.client.get('/api/analysis/export/test_id/')

        # التأكد من إرسال الإشعار
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['file_type'], 'PDF')
```

## 📈 مراقبة الأداء

### Metrics Collection
```python
# في Notification Service
from django_prometheus.exports import ExportToDjangoView

# إضافة metrics للتكامل
NOTIFICATION_INTEGRATION_METRICS = {
    'upm_requests_total': 0,
    'ai_requests_total': 0,
    'failed_requests_total': 0,
    'response_time_avg': 0,
}

def track_integration_metrics(system, success, response_time):
    """تتبع مقاييس التكامل"""
    if system == 'upm':
        NOTIFICATION_INTEGRATION_METRICS['upm_requests_total'] += 1
    elif system == 'ai':
        NOTIFICATION_INTEGRATION_METRICS['ai_requests_total'] += 1

    if not success:
        NOTIFICATION_INTEGRATION_METRICS['failed_requests_total'] += 1

    # حساب متوسط وقت الاستجابة
    total_requests = (NOTIFICATION_INTEGRATION_METRICS['upm_requests_total'] +
                     NOTIFICATION_INTEGRATION_METRICS['ai_requests_total'])
    if total_requests > 0:
        current_avg = NOTIFICATION_INTEGRATION_METRICS['response_time_avg']
        NOTIFICATION_INTEGRATION_METRICS['response_time_avg'] = (
            (current_avg * (total_requests - 1)) + response_time
        ) / total_requests
```

## 🔐 الأمان والمصادقة

### API Key Authentication
```python
# في Notification Service
from rest_framework.permissions import BasePermission

class SystemApiKeyPermission(BasePermission):
    """إذن للمصادقة بين الأنظمة"""

    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key')
        expected_key = getattr(settings, 'SYSTEM_API_KEY', None)

        if not api_key or not expected_key:
            return False

        return api_key == expected_key
```

### استخدام في UPM_Project
```python
# في settings.py
SYSTEM_API_KEY = 'upm-system-key-123'

# في requests
headers = {'X-API-Key': settings.SYSTEM_API_KEY}
response = requests.post(url, json=data, headers=headers)
```

## 🚀 خطة التوسع

### Phase 1: Basic Integration ✅
- تكامل أساسي مع UPM و AI projects
- إشعارات أساسية
- Docker setup

### Phase 2: Advanced Features 🔄
- Circuit breaker pattern
- Metrics collection
- API key authentication
- Bulk notifications

### Phase 3: Production Ready 🚀
- Load balancing
- Database replication
- Monitoring dashboard
- Webhook support

---

## 📞 الدعم والمساعدة

### نقاط الاتصال
- **Notification Service Admin**: http://localhost:8004/admin/
- **API Documentation**: http://localhost:8004/swagger/
- **Health Check**: http://localhost:8004/health/

### استكشاف الأخطاء الشائعة
1. **Connection refused**: تحقق من تشغيل حاوية notification-service
2. **Timeout**: زد قيمة timeout أو استخدم async calls
3. **Email not sending**: تحقق من إعدادات SMTP في .env
4. **Database errors**: تحقق من صحة connection string

### Best Practices
- استخدم timeout قصير (2-3 ثواني) لعدم تأثير على الأداء
- لا تتوقف العمليات الرئيسية عند فشل الإشعارات
- استخدم background tasks للإشعارات الثقيلة
- راقب معدل النجاح والأداء

**التكامل جاهز للاستخدام! 🎯**
