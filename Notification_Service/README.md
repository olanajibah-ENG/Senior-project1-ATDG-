# 📧 Notification Service - خدمة الإشعارات

خدمة مستقلة لإرسال الإشعارات عبر البريد الإلكتروني مع دعم القوالب والطوابير.

## 📋 المحتويات

- [الميزات](#-الميزات)
- [التثبيت](#-التثبيت)
- [الاستخدام](#-الاستخدام)
- [API Documentation](#-api-documentation)
- [البنية](#-البنية)

## ✨ الميزات

### 📨 إرسال الإشعارات
- إرسال بريد إلكتروني
- دعم HTML و Plain Text
- مرفقات الملفات
- إرسال جماعي (Bulk)

### 📋 نظام القوالب
- قوالب قابلة للتخصيص
- متغيرات ديناميكية
- دعم HTML Templates
- معاينة القوالب

### 🔄 إدارة الطوابير
- Celery للمهام غير المتزامنة
- Redis كـ Message Broker
- إعادة المحاولة التلقائية
- تتبع حالة الإرسال

### 📊 التتبع والإحصائيات
- سجل الإشعارات
- حالة التسليم
- معدل النجاح
- تقارير الأخطاء

## 🚀 التثبيت

### المتطلبات
- Python 3.8+
- PostgreSQL
- Redis
- Gmail Account (أو SMTP Server)

### 1. تثبيت المتطلبات

```bash
cd Notification_Service
pip install -r requirements.txt
```

### 2. إعداد المتغيرات البيئية

```bash
# في ملف .env الرئيسي
NOTIFICATION_DJANGO_SECRET_KEY=your-secret-key
NOTIFICATION_DJANGO_PORT=8004

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=notification_service_db
DB_USER=notification_user
DB_PASSWORD=your-password
DB_HOST=notification_db
DB_PORT=5432

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=AutoTest & DocGen <your-email@gmail.com>

# Redis
REDIS_URL=redis://notification_redis:6379/0
```

### 3. إنشاء قاعدة البيانات

```bash
# إنشاء قاعدة البيانات
psql -U postgres
CREATE DATABASE notification_service_db;
CREATE USER notification_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE notification_service_db TO notification_user;
```

### 4. تطبيق Migrations

```bash
python manage.py migrate
```

### 5. تشغيل السيرفر

```bash
# Django Server
python manage.py runserver 0.0.0.0:8004

# Celery Worker (في terminal آخر)
celery -A notification_service worker -l info
```

## 📖 الاستخدام

### 1. إرسال إشعار بسيط

```bash
curl -X POST http://localhost:8004/api/notifications/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Welcome to AutoTest & DocGen",
    "message": "Thank you for registering!",
    "notification_type": "email"
  }'
```

**Response:**
```json
{
  "id": 1,
  "status": "PENDING",
  "message": "Notification queued successfully"
}
```

### 2. إرسال إشعار مع قالب

```bash
curl -X POST http://localhost:8004/api/notifications/send-template/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "template_name": "welcome_email",
    "context": {
      "username": "John Doe",
      "activation_link": "https://example.com/activate/123"
    }
  }'
```

### 3. التحقق من حالة الإشعار

```bash
curl -X GET http://localhost:8004/api/notifications/1/status/
```

**Response:**
```json
{
  "id": 1,
  "status": "SENT",
  "sent_at": "2026-01-03T10:30:00Z",
  "attempts": 1
}
```

### 4. إرسال جماعي

```bash
curl -X POST http://localhost:8004/api/notifications/bulk-send/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["user1@example.com", "user2@example.com"],
    "subject": "System Update",
    "message": "The system will be updated tonight."
  }'
```

## 📚 API Documentation

### Notification Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/notifications/send/` | POST | إرسال إشعار |
| `/api/notifications/send-template/` | POST | إرسال مع قالب |
| `/api/notifications/bulk-send/` | POST | إرسال جماعي |
| `/api/notifications/{id}/` | GET | تفاصيل إشعار |
| `/api/notifications/{id}/status/` | GET | حالة الإشعار |
| `/api/notifications/` | GET | قائمة الإشعارات |

### Template Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/templates/` | GET | قائمة القوالب |
| `/api/templates/` | POST | إنشاء قالب |
| `/api/templates/{id}/` | GET | تفاصيل قالب |
| `/api/templates/{id}/` | PUT | تحديث قالب |
| `/api/templates/{id}/preview/` | POST | معاينة قالب |

### Statistics Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/stats/` | GET | إحصائيات عامة |
| `/api/stats/daily/` | GET | إحصائيات يومية |
| `/api/stats/success-rate/` | GET | معدل النجاح |

## 🏗️ البنية

```
Notification_Service/
├── notifications/               # التطبيق الرئيسي
│   ├── models.py               # نماذج البيانات
│   │   ├── Notification       # نموذج الإشعار
│   │   ├── NotificationTemplate # نموذج القالب
│   │   └── NotificationLog    # سجل الإشعارات
│   ├── views.py                # API Views
│   ├── serializers.py          # Django REST Serializers
│   ├── tasks.py                # Celery Tasks
│   ├── email_service.py        # خدمة البريد
│   └── urls.py                 # URL Routing
├── notification_service/        # إعدادات Django
│   ├── settings.py            # الإعدادات الرئيسية
│   ├── celery.py              # إعدادات Celery
│   └── urls.py                # URL الرئيسي
├── templates/                   # قوالب البريد
│   └── email/                  # قوالب HTML
├── manage.py                    # Django Management
├── requirements.txt             # المتطلبات
└── README.md                    # هذا الملف
```

## 🔧 التطوير

### إنشاء قالب جديد

```python
# notifications/models.py
template = NotificationTemplate.objects.create(
    name='password_reset',
    subject='Reset Your Password',
    html_content='''
        <h1>Password Reset</h1>
        <p>Hello {{ username }},</p>
        <p>Click the link below to reset your password:</p>
        <a href="{{ reset_link }}">Reset Password</a>
    ''',
    variables=['username', 'reset_link']
)
```

### إضافة Celery Task

```python
# notifications/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_notification_task(self, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        # إرسال الإشعار
        send_email(notification)
        notification.status = 'SENT'
        notification.save()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### تخصيص خدمة البريد

```python
# notifications/email_service.py
from django.core.mail import EmailMultiAlternatives

def send_html_email(recipient, subject, html_content, text_content=None):
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content or '',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
```

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
python manage.py test

# اختبار محدد
python manage.py test notifications.tests.test_email_service

# مع coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔐 الأمان

### Gmail App Password

1. تفعيل 2FA في حساب Gmail
2. إنشاء App Password:
   - https://myaccount.google.com/apppasswords
3. استخدام App Password في `.env`

```bash
EMAIL_HOST_PASSWORD=your-16-digit-app-password
```

### Rate Limiting

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## 📊 قاعدة البيانات

### Schema

```sql
-- Notifications Table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient VARCHAR(254),
    subject VARCHAR(200),
    message TEXT,
    html_content TEXT,
    notification_type VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP,
    sent_at TIMESTAMP,
    attempts INTEGER DEFAULT 0
);

-- Notification Templates Table
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    subject VARCHAR(200),
    html_content TEXT,
    text_content TEXT,
    variables JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Notification Logs Table
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id)
);
```

## 🐛 استكشاف الأخطاء

### مشكلة: فشل إرسال البريد

```bash
# تحقق من إعدادات SMTP
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### مشكلة: Celery لا يعمل

```bash
# تحقق من Redis
redis-cli ping

# تحقق من Celery workers
celery -A notification_service inspect active

# إعادة تشغيل Celery
celery -A notification_service worker -l info --purge
```

### مشكلة: بطء في الإرسال

```bash
# زيادة عدد workers
celery -A notification_service worker -l info --concurrency=4

# استخدام Celery Beat للمهام الدورية
celery -A notification_service beat -l info
```

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المشروع
2. إنشاء branch للميزة
3. Commit التغييرات
4. فتح Pull Request

## 📞 الدعم

- **Issues**: افتح issue في GitHub
- **Documentation**: راجع التوثيق
- **Logs**: تحقق من logs/notification_service.log

---

**آخر تحديث:** يناير 2026  
**الإصدار:** 2.0
