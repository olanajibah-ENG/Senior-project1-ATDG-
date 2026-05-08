# 🤖 AutoTest & DocGen - نظام توليد التوثيق التلقائي

نظام شامل لتحليل الكود البرمجي وإنشاء توثيق تقني احترافي باستخدام الذكاء الاصطناعي.

## 📋 نظرة عامة

يتكون المشروع من 3 خدمات رئيسية:
- **AI Project**: نظام الذكاء الاصطناعي لتحليل الكود وتوليد التوثيق
- **UPM Project**: نظام إدارة المشاريع والمستخدمين
- **Notification Service**: خدمة الإشعارات عبر البريد الإلكتروني

## 🏗️ هيكل المشروع

```
AutoTest&DocGen/
├── Ai_project/              # 🧠 نظام الذكاء الاصطناعي
├── UPM_Project/             # 📊 إدارة المشاريع
├── Notification_Service/    # 📧 خدمة الإشعارات
├── FrontEnd/                # 💻 الواجهة الأمامية
├── nginx/                   # 🌐 Reverse Proxy
├── .env                     # 🔐 المتغيرات البيئية
├── .env.example             # 📝 قالب المتغيرات
├── docker-compose.yml       # 🐳 Docker Configuration
└── README.md                # 📖 هذا الملف
```

## 🚀 البدء السريع

### المتطلبات
- Docker & Docker Compose
- Python 3.8+
- Node.js 16+ (للواجهة الأمامية)

### 1. إعداد المتغيرات البيئية

```bash
# انسخ ملف القالب
cp .env.example .env

# عدّل المتغيرات حسب بيئتك
nano .env
```

### 2. تشغيل المشروع

```bash
# تشغيل جميع الخدمات
docker-compose up -d

# أو تشغيل خدمة محددة
docker-compose up -d ai_web
```

### 3. الوصول للخدمات

- **AI Project**: http://localhost:8002
- **UPM Project**: http://localhost:8001
- **Notification Service**: http://localhost:8004
- **Frontend**: http://localhost:3000

## 📚 التوثيق التفصيلي

### AI Project
راجع [Ai_project/README.md](Ai_project/README.md) للتفاصيل الكاملة:
- تحليل الكود (Java, Python)
- توليد التوثيق (High/Low Level)
- تصدير PDF/Markdown
- API Documentation

### UPM Project
راجع [UPM_Project/README.md](UPM_Project/README.md) للتفاصيل:
- إدارة المشاريع
- إدارة المستخدمين
- التكامل مع AI Service

### Notification Service
راجع [Notification_Service/README.md](Notification_Service/README.md) للتفاصيل:
- إرسال الإشعارات
- قوالب البريد الإلكتروني
- إدارة الطوابير

## 🔐 الأمان

### المتغيرات البيئية

جميع المفاتيح السرية موجودة في ملف `.env`:

```bash
# Django Secret Keys
AI_DJANGO_SECRET_KEY=your-secret-key
UPM_DJANGO_SECRET_KEY=your-secret-key
NOTIFICATION_DJANGO_SECRET_KEY=your-secret-key

# API Keys
OPENROUTER_API_KEY=your-api-key
AI_SERVICE_KEY=your-service-key

# Database Passwords
MYSQL_PASSWORD=your-password
DB_PASSWORD=your-password
```

### توليد مفاتيح قوية

```bash
# استخدم السكريبت المرفق
python generate_secret_keys.py

# أو استخدم Python مباشرة
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### التحقق من الأمان

```bash
# فحص المتغيرات البيئية
python check_env.py
```

## 🛠️ التطوير

### تثبيت المتطلبات

```bash
# AI Project
cd Ai_project
pip install -r requirements.txt

# UPM Project
cd UPM_Project
pip install -r requirements.txt

# Notification Service
cd Notification_Service
pip install -r requirements.txt
```

### تشغيل الاختبارات

```bash
# AI Project
cd Ai_project
python manage.py test

# UPM Project
cd UPM_Project
python manage.py test
```

### فحص Django

```bash
# فحص الإعدادات
python manage.py check

# فحص الأمان
python manage.py check --deploy
```

## 📊 قواعد البيانات

- **MySQL**: UPM Project
- **PostgreSQL**: Notification Service
- **MongoDB**: AI Project (تخزين التحليلات)
- **Redis**: Celery (المهام غير المتزامنة)

### Migrations

```bash
# تطبيق migrations
python manage.py migrate

# إنشاء migrations جديدة
python manage.py makemigrations
```

## 🐳 Docker

### بناء الصور

```bash
# بناء جميع الصور
docker-compose build

# بناء صورة محددة
docker-compose build ai_web
```

### إدارة الحاويات

```bash
# عرض الحاويات
docker-compose ps

# عرض اللوجات
docker-compose logs -f ai_web

# إيقاف الخدمات
docker-compose down

# إيقاف وحذف البيانات
docker-compose down -v
```

## 🔧 استكشاف الأخطاء

### مشاكل شائعة

#### 1. خطأ في الاتصال بقاعدة البيانات
```bash
# تحقق من تشغيل قاعدة البيانات
docker-compose ps

# أعد تشغيل الخدمة
docker-compose restart mysql
```

#### 2. خطأ في المتغيرات البيئية
```bash
# تحقق من المتغيرات
python check_env.py

# تأكد من وجود .env
ls -la .env
```

#### 3. خطأ في المنافذ
```bash
# تحقق من المنافذ المستخدمة
netstat -tulpn | grep :8002

# غيّر المنفذ في .env
AI_DJANGO_PORT=8003
```

## 🧪 اختبار الروابط والـ APIs

تم إنشاء مجموعة شاملة من الأدوات والتوثيق لاختبار جميع روابط النظام:

### 📚 التوثيق الشامل
- **[SYSTEM_URLS_DOCUMENTATION.md](SYSTEM_URLS_DOCUMENTATION.md)** - توثيق كامل لجميع الـ APIs
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - أمثلة عملية جاهزة للتنفيذ
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - دليل شامل للاختبار
- **[URL_TESTING_INDEX.md](URL_TESTING_INDEX.md)** - فهرس شامل لجميع الموارد

### 🧪 أدوات الاختبار
```bash
# اختبار شامل باستخدام Python
python test_all_urls.py

# اختبار سريع باستخدام Bash
bash test_urls.sh

# عرض النتائج في المتصفح
start test_results.html
```

### 📊 نتائج الاختبار الأخيرة
- ✅ **17/17** اختبار نجح
- ✅ **100%** نسبة النجاح
- ✅ جميع الخدمات تعمل بشكل صحيح

**للمزيد من التفاصيل:** راجع [URL_TESTING_SUMMARY.md](URL_TESTING_SUMMARY.md)

---

## 📝 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المشروع
2. إنشاء branch للميزة الجديدة
3. Commit التغييرات
4. Push وفتح Pull Request

## 📞 الدعم

- **التوثيق**: راجع ملفات README في كل مشروع
- **اختبار الـ APIs**: راجع [SYSTEM_URLS_DOCUMENTATION.md](SYSTEM_URLS_DOCUMENTATION.md)
- **المشاكل**: افتح Issue في GitHub
- **الأمان**: راجع `check_env.py` و `.env.example`

---

**آخر تحديث:** يناير 2026  
**الإصدار:** 2.0
