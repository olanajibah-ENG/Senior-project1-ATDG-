# 🔗 توثيق شامل لجميع روابط النظام

## 📋 نظرة عامة

هذا الملف يحتوي على جميع الروابط والـ Endpoints المتاحة في نظام AutoTest & DocGen.

---

## 🌐 الوصول عبر Nginx Gateway (المنفذ 80)

### 🔐 المصادقة والتوكن (JWT)

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `http://localhost/api/token/` | POST | الحصول على Access & Refresh Token |
| `http://localhost/api/token/refresh/` | POST | تحديث Access Token |
| `http://localhost/api/token/verify/` | POST | التحقق من صلاحية Token |

**مثال طلب الحصول على Token:**
```bash
curl -X POST http://localhost/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'
```

---

## 📊 UPM Project - إدارة المشاريع والمستخدمين

### الوصول المباشر: `http://localhost:8001`
### الوصول عبر Gateway: `http://localhost/api/upm/`

### 👤 إدارة المستخدمين

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/upm/signup/` | POST | تسجيل مستخدم جديد |
| `/api/upm/login/` | POST | تسجيل الدخول |

**مثال التسجيل:**
```bash
curl -X POST http://localhost/api/upm/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "Ahmed",
    "last_name": "Ali"
  }'
```

### 📁 إدارة المشاريع

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/upm/projects/` | GET | قائمة جميع المشاريع |
| `/api/upm/projects/` | POST | إنشاء مشروع جديد |
| `/api/upm/projects/{project_id}/` | GET | تفاصيل مشروع محدد |
| `/api/upm/projects/{project_id}/` | PUT/PATCH | تحديث مشروع |
| `/api/upm/projects/{project_id}/` | DELETE | حذف مشروع |

**مثال إنشاء مشروع:**
```bash
curl -X POST http://localhost/api/upm/projects/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Project description",
    "language": "python"
  }'
```

### 📄 إدارة الملفات البرمجية (Artifacts)

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/upm/projects/{project_id}/artifacts/` | GET | قائمة ملفات المشروع |
| `/api/upm/projects/{project_id}/artifacts/` | POST | رفع ملف جديد |
| `/api/upm/artifacts/{code_id}/` | GET | تفاصيل ملف محدد |
| `/api/upm/artifacts/{code_id}/` | PUT/PATCH | تحديث ملف |
| `/api/upm/artifacts/{code_id}/` | DELETE | حذف ملف |

**مثال رفع ملف:**
```bash
curl -X POST http://localhost/api/upm/projects/{project_id}/artifacts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/code.py" \
  -F "file_name=code.py" \
  -F "language=python"
```

### 📚 التوثيق التفاعلي

| الرابط | الوصف |
|--------|-------|
| `http://localhost/swagger-upm/` | Swagger UI للتوثيق التفاعلي |
| `http://localhost/redoc-upm/` | ReDoc للتوثيق |
| `http://localhost:8001/admin/` | لوحة تحكم Django Admin |

---

## 🧠 AI Project - تحليل الكود والذكاء الاصطناعي

### الوصول المباشر: `http://localhost:8002`
### الوصول عبر Gateway: `http://localhost/api/analysis/`

### 📝 إدارة ملفات الكود

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/analysis/codefiles/` | GET | قائمة جميع ملفات الكود |
| `/api/analysis/codefiles/` | POST | رفع ملف كود جديد |
| `/api/analysis/codefiles/{id}/` | GET | تفاصيل ملف محدد |
| `/api/analysis/codefiles/{id}/` | PUT/PATCH | تحديث ملف |
| `/api/analysis/codefiles/{id}/` | DELETE | حذف ملف |

**مثال رفع ملف للتحليل:**
```bash
curl -X POST http://localhost/api/analysis/codefiles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/code.java" \
  -F "language=java" \
  -F "project_id=PROJECT_UUID"
```

### 🔍 وظائف التحليل (Analysis Jobs)

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/analysis/analysis-jobs/` | GET | قائمة جميع وظائف التحليل |
| `/api/analysis/analysis-jobs/` | POST | إنشاء وظيفة تحليل جديدة |
| `/api/analysis/analysis-jobs/{id}/` | GET | تفاصيل وظيفة محددة |
| `/api/analysis/analysis-jobs/{id}/status/` | GET | حالة التحليل |
| `/api/analysis/analysis-jobs/{id}/cancel/` | POST | إلغاء التحليل |

**مثال بدء تحليل:**
```bash
curl -X POST http://localhost/api/analysis/analysis-jobs/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_file_id": "FILE_ID",
    "analysis_type": "high_level",
    "language": "java"
  }'
```

### 📊 نتائج التحليل (Analysis Results)

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/analysis/analysis-results/` | GET | قائمة جميع النتائج |
| `/api/analysis/analysis-results/{id}/` | GET | تفاصيل نتيجة محددة |
| `/api/analysis/analysis-results/{id}/summary/` | GET | ملخص النتيجة |

### 🤖 شروحات الذكاء الاصطناعي

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/analysis/ai-explanations/` | GET | قائمة جميع الشروحات |
| `/api/analysis/ai-explanations/` | POST | طلب شرح جديد |
| `/api/analysis/ai-explanations/{id}/` | GET | تفاصيل شرح محدد |

**مثال طلب شرح:**
```bash
curl -X POST http://localhost/api/analysis/ai-explanations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_snippet": "public class Main { ... }",
    "question": "ما هي وظيفة هذا الكود؟",
    "language": "java"
  }'
```

### 📤 تصدير التوثيق

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/analysis/export/{analysis_id}/` | GET | تصدير التوثيق (PDF/Markdown) |
| `/api/analysis/generated-files/` | GET | قائمة الملفات المولدة |
| `/api/analysis/download-generated-file/{file_id}/` | GET | تحميل ملف مولد |

**مثال تصدير PDF:**
```bash
curl -X GET "http://localhost/api/analysis/export/ANALYSIS_ID/?format=pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output documentation.pdf
```

**مثال تصدير Markdown:**
```bash
curl -X GET "http://localhost/api/analysis/export/ANALYSIS_ID/?format=markdown" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output documentation.md
```

### 📚 التوثيق التفاعلي

| الرابط | الوصف |
|--------|-------|
| `http://localhost/swagger-ai/` | Swagger UI للتوثيق التفاعلي |
| `http://localhost/redoc-ai/` | ReDoc للتوثيق |
| `http://localhost/admin-ai/` | لوحة تحكم Django Admin |

---

## 📧 Notification Service - خدمة الإشعارات

### الوصول المباشر: `http://localhost:8004`
### الوصول عبر Gateway: `http://localhost/api/notifications/`

### 📬 إنشاء الإشعارات

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/notifications/project/` | POST | إشعار متعلق بمشروع |
| `/api/notifications/code/` | POST | إشعار متعلق بملف كود |
| `/api/notifications/documentation/` | POST | إشعار متعلق بتوثيق |
| `/api/notifications/user/` | POST | إشعار للمستخدم |
| `/api/notifications/system/` | POST | تنبيه نظامي |
| `/api/notifications/custom/` | POST | إشعار مخصص |

**مثال إرسال إشعار مشروع:**
```bash
curl -X POST http://localhost/api/notifications/project/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_UUID",
    "user_email": "user@example.com",
    "notification_type": "project_created",
    "message": "تم إنشاء المشروع بنجاح"
  }'
```

**مثال إرسال إشعار توثيق:**
```bash
curl -X POST http://localhost/api/notifications/documentation/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "ANALYSIS_ID",
    "user_email": "user@example.com",
    "notification_type": "documentation_ready",
    "documentation_url": "http://example.com/docs/file.pdf"
  }'
```

### ⚙️ إعدادات الإشعارات

| الرابط | الطريقة | الوصف |
|--------|---------|-------|
| `/api/notifications/settings/` | GET | الحصول على إعدادات المستخدم |
| `/api/notifications/settings/` | POST | تحديث إعدادات الإشعارات |

**مثال تحديث الإعدادات:**
```bash
curl -X POST http://localhost/api/notifications/settings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email_notifications": true,
    "project_notifications": true,
    "documentation_notifications": true
  }'
```

### 📚 التوثيق التفاعلي

| الرابط | الوصف |
|--------|-------|
| `http://localhost:8004/swagger/` | Swagger UI للتوثيق التفاعلي |
| `http://localhost:8004/redoc/` | ReDoc للتوثيق |
| `http://localhost:8004/admin/` | لوحة تحكم Django Admin |

---

## 🏥 Health Check Endpoints

| الخدمة | الرابط | الوصف |
|--------|--------|-------|
| UPM | `http://localhost:8001/health/` | فحص صحة خدمة UPM |
| AI | `http://localhost:8002/health/` | فحص صحة خدمة AI |
| Notification | `http://localhost:8004/health/` | فحص صحة خدمة الإشعارات |

**مثال فحص الصحة:**
```bash
curl http://localhost:8001/health/
# Response: OK

curl http://localhost:8004/health/
# Response: {"status": "healthy", "service": "notification-service"}
```

---

## 🔧 Admin Panels

| الخدمة | الرابط | الوصف |
|--------|--------|-------|
| UPM Admin | `http://localhost/admin/` | لوحة تحكم UPM |
| AI Admin | `http://localhost/admin-ai/` | لوحة تحكم AI |
| Notification Admin | `http://localhost:8004/admin/` | لوحة تحكم الإشعارات |

---

## 🧪 اختبار الروابط

### سكريبت Python لاختبار جميع الروابط:

```python
import requests

# قائمة الروابط للاختبار
endpoints = {
    "UPM Health": "http://localhost:8001/health/",
    "AI Health": "http://localhost:8002/health/",
    "Notification Health": "http://localhost:8004/health/",
    "UPM Swagger": "http://localhost/swagger-upm/",
    "AI Swagger": "http://localhost/swagger-ai/",
    "Gateway": "http://localhost/",
}

print("🧪 اختبار الروابط...\n")

for name, url in endpoints.items():
    try:
        response = requests.get(url, timeout=5)
        status = "✅" if response.status_code < 400 else "❌"
        print(f"{status} {name}: {url} - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: {url} - Error: {str(e)}")
```

### سكريبت Bash لاختبار الروابط:

```bash
#!/bin/bash

echo "🧪 اختبار الروابط..."
echo ""

# Health checks
echo "📊 Health Checks:"
curl -s http://localhost:8001/health/ && echo " ✅ UPM Health" || echo " ❌ UPM Health"
curl -s http://localhost:8002/health/ && echo " ✅ AI Health" || echo " ❌ AI Health"
curl -s http://localhost:8004/health/ && echo " ✅ Notification Health" || echo " ❌ Notification Health"

echo ""
echo "📚 Documentation:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/swagger-upm/ && echo " ✅ UPM Swagger" || echo " ❌ UPM Swagger"
curl -s -o /dev/null -w "%{http_code}" http://localhost/swagger-ai/ && echo " ✅ AI Swagger" || echo " ❌ AI Swagger"

echo ""
echo "🔐 Admin Panels:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/ && echo " ✅ UPM Admin" || echo " ❌ UPM Admin"
curl -s -o /dev/null -w "%{http_code}" http://localhost/admin-ai/ && echo " ✅ AI Admin" || echo " ❌ AI Admin"
```

---

## 📝 ملاحظات مهمة

### 🔐 المصادقة
- معظم الـ Endpoints تتطلب JWT Token
- احصل على Token من `/api/token/`
- أضف Token في Header: `Authorization: Bearer YOUR_TOKEN`

### 🌐 CORS
- تأكد من إعدادات CORS في حالة استخدام Frontend منفصل
- الإعدادات موجودة في `settings.py` لكل خدمة

### 🐳 Docker
- تأكد من تشغيل جميع الخدمات: `docker-compose ps`
- راجع اللوجات في حالة وجود مشاكل: `docker-compose logs -f`

### 📊 قواعد البيانات
- UPM: MySQL على المنفذ 3307
- AI: MongoDB على المنفذ 27017
- Notification: Redis على المنفذ 6380

---

## 🔗 روابط سريعة

### للمطورين:
- [README الرئيسي](README.md)
- [هيكل المشروع](PROJECT_STRUCTURE.md)
- [دليل Docker](DOCKER_README.md)

### التوثيق التفصيلي:
- [AI Project README](Ai_project/README.md)
- [UPM Project README](UPM_Project/README.md)
- [Notification Service README](Notification_Service/README.md)

---

**آخر تحديث:** يناير 2026  
**الإصدار:** 2.0
