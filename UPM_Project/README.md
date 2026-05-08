# 📊 UPM Project - نظام إدارة المشاريع والمستخدمين

نظام شامل لإدارة المشاريع والمستخدمين مع التكامل مع خدمة الذكاء الاصطناعي.

## 📋 المحتويات

- [الميزات](#-الميزات)
- [التثبيت](#-التثبيت)
- [الاستخدام](#-الاستخدام)
- [API Documentation](#-api-documentation)
- [البنية](#-البنية)

## ✨ الميزات

### 👥 إدارة المستخدمين
- تسجيل وتسجيل دخول المستخدمين
- JWT Authentication
- إدارة الصلاحيات
- ملفات المستخدمين

### 📁 إدارة المشاريع
- إنشاء وتعديل المشاريع
- ربط المشاريع بالمستخدمين
- تتبع حالة المشاريع
- إحصائيات المشاريع

### 🔗 التكامل مع AI Service
- إرسال الكود للتحليل
- استقبال نتائج التحليل
- ربط التحليلات بالمشاريع

### 📧 نظام الإشعارات
- إشعارات البريد الإلكتروني
- إشعارات داخل النظام
- قوالب قابلة للتخصيص

## 🚀 التثبيت

### المتطلبات
- Python 3.8+
- MySQL 5.7+
- Redis

### 1. تثبيت المتطلبات

```bash
cd UPM_Project
pip install -r requirements.txt
```

### 2. إعداد المتغيرات البيئية

```bash
# في ملف .env الرئيسي
UPM_DJANGO_SECRET_KEY=your-secret-key
UPM_DJANGO_PORT=8001
MYSQL_DATABASE=upm_mysql_db
MYSQL_USER=admin3
MYSQL_PASSWORD=your-password
MYSQL_PORT=3307
```

### 3. إنشاء قاعدة البيانات

```bash
# إنشاء قاعدة البيانات
mysql -u root -p
CREATE DATABASE upm_mysql_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admin3'@'%' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON upm_mysql_db.* TO 'admin3'@'%';
FLUSH PRIVILEGES;
```

### 4. تطبيق Migrations

```bash
python manage.py migrate
```

### 5. إنشاء superuser

```bash
python manage.py createsuperuser
```

### 6. تشغيل السيرفر

```bash
python manage.py runserver 0.0.0.0:8001
```

## 📖 الاستخدام

### 1. تسجيل مستخدم جديد

```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. تسجيل الدخول

```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### 3. إنشاء مشروع

```bash
curl -X POST http://localhost:8001/api/projects/ \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-Commerce Platform",
    "description": "Online shopping platform",
    "status": "active"
  }'
```

### 4. إرسال كود للتحليل

```bash
curl -X POST http://localhost:8001/api/projects/1/analyze-code/ \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "ProductManager.java",
    "file_type": "java",
    "content": "public class ProductManager { ... }"
  }'
```

## 📚 API Documentation

### Authentication Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/auth/register/` | POST | تسجيل مستخدم جديد |
| `/api/auth/login/` | POST | تسجيل الدخول |
| `/api/auth/logout/` | POST | تسجيل الخروج |
| `/api/auth/refresh/` | POST | تحديث JWT Token |
| `/api/auth/profile/` | GET | الحصول على الملف الشخصي |

### Projects Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/projects/` | GET | قائمة المشاريع |
| `/api/projects/` | POST | إنشاء مشروع |
| `/api/projects/{id}/` | GET | تفاصيل مشروع |
| `/api/projects/{id}/` | PUT | تحديث مشروع |
| `/api/projects/{id}/` | DELETE | حذف مشروع |
| `/api/projects/{id}/analyze-code/` | POST | تحليل كود |

### Users Endpoints

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/users/` | GET | قائمة المستخدمين |
| `/api/users/{id}/` | GET | تفاصيل مستخدم |
| `/api/users/{id}/` | PUT | تحديث مستخدم |
| `/api/users/{id}/projects/` | GET | مشاريع المستخدم |

## 🏗️ البنية

```
UPM_Project/
├── core_upm/                    # التطبيق الرئيسي
│   ├── models.py               # نماذج البيانات
│   │   ├── User               # نموذج المستخدم
│   │   ├── Project            # نموذج المشروع
│   │   └── ProjectMember      # أعضاء المشروع
│   ├── views.py                # API Views
│   ├── serializers.py          # Django REST Serializers
│   ├── permissions.py          # صلاحيات مخصصة
│   └── urls.py                 # URL Routing
├── UPM_Project/                # إعدادات Django
│   ├── settings.py            # الإعدادات الرئيسية
│   └── urls.py                # URL الرئيسي
├── staticfiles/                # ملفات ثابتة
├── manage.py                   # Django Management
├── requirements.txt            # المتطلبات
└── README.md                   # هذا الملف
```

## 🔧 التطوير

### إضافة نموذج جديد

```python
# core_upm/models.py
from django.db import models

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
```

### إضافة API endpoint

```python
# core_upm/views.py
from rest_framework import viewsets

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
```

### إضافة صلاحيات مخصصة

```python
# core_upm/permissions.py
from rest_framework import permissions

class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
```

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
python manage.py test

# اختبار محدد
python manage.py test core_upm.tests.test_projects

# مع coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔐 الأمان

### المفاتيح المطلوبة

```bash
# في .env
UPM_DJANGO_SECRET_KEY=your-strong-secret-key
AI_SERVICE_KEY=your-service-key
MYSQL_PASSWORD=your-password
```

### JWT Configuration

```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### CORS Settings

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📊 قاعدة البيانات

### Schema

```sql
-- Users Table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE,
    email VARCHAR(254) UNIQUE,
    password VARCHAR(128),
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    created_at DATETIME,
    updated_at DATETIME
);

-- Projects Table
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200),
    description TEXT,
    owner_id INT,
    status VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- Project Members Table
CREATE TABLE project_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT,
    user_id INT,
    role VARCHAR(20),
    joined_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Migrations

```bash
# إنشاء migrations
python manage.py makemigrations

# تطبيق migrations
python manage.py migrate

# عرض SQL
python manage.py sqlmigrate core_upm 0001
```

## 🐛 استكشاف الأخطاء

### مشكلة: خطأ في الاتصال بقاعدة البيانات

```bash
# تحقق من MySQL
mysql -u admin3 -p -h localhost -P 3307

# تحقق من الإعدادات
python manage.py dbshell
```

### مشكلة: خطأ في JWT Token

```bash
# تحقق من صلاحية Token
python manage.py shell
>>> from rest_framework_simplejwt.tokens import AccessToken
>>> token = AccessToken('your-token')
>>> print(token.payload)
```

### مشكلة: خطأ في CORS

```bash
# أضف النطاق في settings.py
CORS_ALLOWED_ORIGINS = [
    "http://your-frontend-domain.com",
]
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
- **Logs**: تحقق من logs/upm_project.log

---

**آخر تحديث:** يناير 2026  
**الإصدار:** 2.0
