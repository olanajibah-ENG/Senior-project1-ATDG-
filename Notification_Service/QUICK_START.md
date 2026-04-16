# 🚀 دليل البدء السريع - Notification Service

## المتطلبات
- Docker & Docker Compose
- Git
- متصفح ويب

## 1. إعداد المشروع

### استنساخ أو إنشاء المجلد
```bash
cd Kamar_11_2025
# المجلد موجود بالفعل في: Notification_Service/
```

### إعداد متغيرات البيئة
```bash
cd Notification_Service
# ملف البيئة جاهز: environment
```

### تعديل إعدادات الإيميل (اختياري)
```bash
nano environment
# غيّر الإعدادات التالية إذا كنت تريد إرسال إيميل حقيقي:
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

**ملاحظة**: النظام يعمل بدون إعدادات إيميل - سيقوم بمحاكاة الإرسال فقط

## 2. تشغيل النظام

### باستخدام Docker Compose
```bash
# تشغيل جميع الخدمات
docker-compose up --build

# أو في الخلفية
docker-compose up -d --build
```

### فحص الخدمات
```bash
# عرض حالة الحاويات
docker-compose ps

# عرض السجلات
docker-compose logs notification_service
```

## 3. الوصول للنظام

### Django Admin
- **URL**: http://localhost:8004/admin/
- **Username**: admin
- **Password**: admin123

### API Documentation
- **Swagger**: http://localhost:8004/swagger/
- **ReDoc**: http://localhost:8004/redoc/

### Health Check
```bash
curl http://localhost:8004/health/
```

## 4. اختبار الـ API

### إرسال إشعار تجريبي
```bash
curl -X POST http://localhost:8004/api/notifications/project/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "action": "created",
    "project_name": "Test Project",
    "project_id": "test_123",
    "user_name": "Test User"
  }'
```

### عرض الإشعارات
```bash
curl http://localhost:8004/api/notifications/notifications/
```

### عرض الإحصائيات
```bash
curl http://localhost:8004/api/notifications/notifications/stats/
```

## 5. التكامل مع النظام الرئيسي

### إضافة في UPM_Project
في ملف `views.py` حيث يتم إنشاء المشاريع:

```python
import requests

def create_project(request):
    # كود إنشاء المشروع...

    # إرسال إشعار
    try:
        requests.post('http://notification-service:8000/api/notifications/project/', json={
            'user_email': request.user.email,
            'action': 'created',
            'project_name': project.name,
            'project_id': str(project.id),
            'user_name': request.user.get_full_name()
        }, timeout=3)
    except:
        pass  # لا تتوقف العملية إذا فشل الإشعار

    return redirect('project_detail', pk=project.id)
```

### إضافة في Ai_Project
في ملف `export_views.py` بعد تصدير الملف:

```python
def export_pdf_with_diagram(request, explanation_id):
    # كود التصدير...

    # إرسال إشعار
    try:
        requests.post('http://notification-service:8000/api/notifications/documentation/', json={
            'user_email': request.user.email,
            'file_name': f'technical_report_{explanation_id}.pdf',
            'file_type': 'PDF',
            'project_name': 'AI Analysis',
            'user_name': request.user.get_full_name()
        }, timeout=3)
    except:
        pass

    return response
```

## 6. مراقبة النظام

### عرض السجلات
```bash
# سجلات Django
docker-compose logs -f notification_service

# سجلات قاعدة البيانات
docker-compose logs -f notification_db

# سجلات Redis
docker-compose logs -f notification_redis
```

### فحص قاعدة البيانات
```bash
# الدخول لحاوية PostgreSQL
docker-compose exec notification_db psql -U notification_user -d notification_service_db

# عرض الجداول
\d

# عرض الإشعارات
SELECT * FROM notifications_notification LIMIT 5;
```

## 7. استكشاف الأخطاء

### إذا لم يعمل Docker
```bash
# إعادة بناء كل شيء
docker-compose down
docker-compose up --build --force-recreate
```

### إذا لم يصل الإيميل
```bash
# فحص إعدادات الإيميل في .env
cat .env | grep EMAIL

# اختبار الإيميل من داخل الحاوية
docker-compose exec notification_service python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'noreply@autotest-docgen.com', ['test@example.com'])
"
```

### إذا كانت قاعدة البيانات لا تعمل
```bash
# إعادة إنشاء قاعدة البيانات
docker-compose exec notification_db dropdb -U notification_user notification_service_db
docker-compose exec notification_db createdb -U notification_user notification_service_db
docker-compose exec notification_service python manage.py migrate
```

## 8. النشر في الإنتاج

### إعدادات الإنتاج
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_HOST=your-production-db-host
EMAIL_HOST_USER=your-production-email@domain.com
```

### استخدام Nginx كـ Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-notification-domain.com;

    location / {
        proxy_pass http://notification_service:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🎯 النصائح المهمة

1. **تأكد من تشغيل جميع الحاويات** قبل الاختبار
2. **إعداد الإيميل ضروري** لعمل الإشعارات
3. **استخدم timeout** في طلبات API لعدم توقف النظام
4. **راقب السجلات** بانتظام للكشف عن المشاكل
5. **عمل نسخة احتياطية** من قاعدة البيانات

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من `docker-compose logs`
2. تأكد من إعدادات `.env`
3. جرب إعادة تشغيل الحاويات
4. راجع `API_DOCUMENTATION.md` للتفاصيل

**النظام جاهز للاستخدام! 🚀**
