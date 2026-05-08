# 📡 Notification Service API Documentation

## نظرة عامة
خدمة RESTful API مبسطة لإرسال الإشعارات في نظام AutoTest & DocGen **بدون تخزين أي بيانات**.

## الأساسيات

### Base URL
```
http://localhost:8004/api/
```

### Authentication
حالياً لا تتطلب Authentication (يمكن إضافة Token authentication لاحقاً)

### Response Format
جميع الاستجابات بصيغة JSON:
```json
{
  "message": "تم إرسال الإشعار بنجاح",
  "status": "SENT",
  "type": "PROJECT_CREATED",
  "title": "عنوان الإشعار"
}
```

---

## 🚀 إرسال الإشعارات

### إشعار إنشاء مشروع
```http
POST /api/notifications/project/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "action": "created",  // أو "deleted"
  "project_name": "My Awesome Project",
  "project_id": "proj_123",
  "user_name": "John Doe"
}
```

**Response (201):**
```json
{
  "message": "تم إرسال الإشعار بنجاح",
  "status": "SENT",
  "type": "PROJECT_CREATED",
  "title": "تم إنشاء مشروع جديد: My Awesome Project"
}
```

### إشعار إضافة/حذف كود
```http
POST /api/notifications/code/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "action": "added",  // أو "deleted"
  "code_name": "main.py",
  "project_name": "My Project",
  "code_id": "code_456",
  "user_name": "John Doe"
}
```

### إشعار تصدير توثيق
```http
POST /api/notifications/documentation/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "file_name": "technical_report.pdf",
  "file_type": "PDF",
  "project_name": "My Project",
  "user_name": "John Doe"
}
```

### إشعار عام
```http
POST /api/notifications/create/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "notification_type": "SYSTEM_ALERT",
  "title": "تنبيه نظام",
  "message": "هذا إشعار تجريبي من النظام",
  "priority": "MEDIUM",
  "related_id": "alert_123",
  "related_type": "system",
  "metadata": {
    "source": "admin",
    "category": "maintenance"
  }
}
```

---

## 📋 إدارة الإشعارات

### عرض جميع الإشعارات
```http
GET /api/notifications/notifications/
```

**Query Parameters:**
- `user_email`: فلترة حسب البريد الإلكتروني
- `type`: فلترة حسب نوع الإشعار
- `status`: فلترة حسب الحالة (PENDING/SENT/FAILED/READ)
- `priority`: فلترة حسب الأولوية

**Example:**
```
GET /api/notifications/notifications/?user_email=user@example.com&type=PROJECT_CREATED&status=SENT
```

### عرض إشعار محدد
```http
GET /api/notifications/notifications/{id}/
```

### تحديد إشعار كمقروء
```http
POST /api/notifications/notifications/{id}/mark_as_read/
```

### إعادة إرسال إشعار
```http
POST /api/notifications/notifications/{id}/resend/
```

---

## 📊 الإحصائيات والمراقبة

### إحصائيات الإشعارات
```http
GET /api/notifications/notifications/stats/
```

**Response:**
```json
{
  "total_notifications": 150,
  "sent_notifications": 145,
  "pending_notifications": 3,
  "failed_notifications": 2,
  "read_notifications": 120,
  "unread_notifications": 30,
  "notifications_today": 12,
  "notifications_this_week": 45,
  "notifications_this_month": 150,
  "by_type": {
    "PROJECT_CREATED": 50,
    "PROJECT_DELETED": 10,
    "CODE_ADDED": 75,
    "CODE_DELETED": 5,
    "DOCUMENTATION_EXPORTED": 10
  },
  "by_priority": {
    "LOW": 20,
    "MEDIUM": 100,
    "HIGH": 25,
    "CRITICAL": 5
  },
  "by_status": {
    "PENDING": 3,
    "SENT": 145,
    "FAILED": 2,
    "READ": 120
  }
}
```

### إعدادات الإشعارات
```http
GET /api/notifications/settings/
```

### تحديد إشعارات متعددة كمقروءة
```http
POST /api/notifications/mark-read/
```

**Request Body:**
```json
{
  "notification_ids": [1, 2, 3, 4, 5],
  "user_email": "user@example.com"
}
```

---

## 🏥 مراقبة الصحة

### فحص حالة الخدمة
```http
GET /health/
```

**Response:**
```json
{
  "status": "healthy",
  "service": "notification-service",
  "database": "connected",
  "email": "configured",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📝 أنواع الإشعارات

| Type | Description | Priority |
|------|-------------|----------|
| `PROJECT_CREATED` | إنشاء مشروع جديد | HIGH |
| `PROJECT_DELETED` | حذف مشروع | HIGH |
| `CODE_ADDED` | إضافة ملف كود | MEDIUM |
| `CODE_DELETED` | حذف ملف كود | MEDIUM |
| `DOCUMENTATION_EXPORTED` | تصدير ملف توثيق | LOW |
| `SYSTEM_ALERT` | تنبيه نظام | CRITICAL |

## 🎯 أولويات الإشعارات

- **LOW**: إشعارات معلوماتية عادية
- **MEDIUM**: إشعارات مهمة تحتاج انتباه
- **HIGH**: إشعارات حرجة تتطلب رد سريع
- **CRITICAL**: إشعارات طوارئ تحتاج تدخل فوري

## 📧 إعدادات الإيميل

### Gmail Configuration
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Outlook Configuration
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

---

## 🔧 استكشاف الأخطاء

### رموز الخطأ الشائعة

| Status Code | Meaning |
|-------------|---------|
| 201 | Created - تم إنشاء الإشعار بنجاح |
| 400 | Bad Request - بيانات غير صحيحة |
| 404 | Not Found - الإشعار غير موجود |
| 500 | Internal Server Error - خطأ في الخادم |

### رسائل الخطأ الشائعة
- `"البيانات المطلوبة: user_email, action, project_name"` - بيانات ناقصة
- `"نوع شرح غير مدعوم"` - نوع إشعار غير صحيح
- `"خطأ في إنشاء الإشعار"` - مشكلة في قاعدة البيانات

---

## 🔗 أمثلة التكامل

### JavaScript (Frontend)
```javascript
// إرسال إشعار مشروع
const sendProjectNotification = async (action, projectData) => {
  try {
    const response = await fetch('/api/notifications/project/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_email: user.email,
        action: action,
        project_name: projectData.name,
        project_id: projectData.id,
        user_name: user.name
      })
    });

    if (response.ok) {
      console.log('Notification sent successfully');
    }
  } catch (error) {
    console.error('Failed to send notification:', error);
  }
};
```

### Python (Backend Integration)
```python
import requests

def notify_project_created(user_email, project_data):
    """إرسال إشعار إنشاء مشروع من النظام الرئيسي"""
    try:
        response = requests.post(
            'http://notification-service:8000/api/notifications/project/',
            json={
                'user_email': user_email,
                'action': 'created',
                'project_name': project_data['name'],
                'project_id': project_data['id'],
                'user_name': project_data.get('owner_name', '')
            },
            timeout=5
        )
        return response.status_code == 201
    except requests.RequestException:
        return False
```

---

## 📚 روابط مفيدة

- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [DRF Yasg Documentation](https://drf-yasg.readthedocs.io/)
- [Django Email Documentation](https://docs.djangoproject.com/en/5.2/topics/email/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

*تم إنشاء هذا التوثيق بواسطة Notification Service v1.0*
