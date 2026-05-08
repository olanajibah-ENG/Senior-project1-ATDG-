# 🧠 AI Project - نظام الذكاء الاصطناعي لتحليل الكود

نظام متقدم لتحليل الكود البرمجي وتوليد توثيق تقني احترافي باستخدام الذكاء الاصطناعي.

## 📋 المحتويات

- [الميزات](#-الميزات)
- [التثبيت](#-التثبيت)
- [الاستخدام](#-الاستخدام)
- [API Documentation](#-api-documentation)
- [البنية](#-البنية)
- [التطوير](#-التطوير)

## ✨ الميزات

### 🤖 تحليل ذكي للكود
- دعم لغات متعددة (Java, Python)
- استخراج تلقائي للفئات والطرق
- تحليل العلاقات (Inheritance, Composition, Association)
- كشف Design Patterns

### 📄 توليد التوثيق
- **High Level**: شرح عام للإدارة والمراجعات
- **Low Level**: شرح تقني مفصل للمطورين
- **Detailed**: شرح شامل مع جميع التفاصيل

### 📊 تصدير احترافي
- **PDF**: تنسيقات جميلة مع ألوان احترافية
- **Markdown**: للمراجعة والتعديل
- **Class Diagrams**: مخططات تفاعلية

### 🔄 معالجة متقدمة
- **AST Analysis**: تحليل بنية الكود
- **Semantic Analysis**: تحليل دلالي للعلاقات
- **Feature Extraction**: استخراج الخصائص والمقاييس

## 🚀 التثبيت

### المتطلبات
- Python 3.8+
- MongoDB
- Redis
- OpenRouter API Key

### 1. تثبيت المتطلبات

```bash
cd Ai_project
pip install -r requirements.txt
```

### 2. إعداد المتغيرات البيئية

```bash
# في ملف .env الرئيسي
AI_DJANGO_SECRET_KEY=your-secret-key
AI_DJANGO_PORT=8002
OPENROUTER_API_KEY=your-api-key
MONGO_HOST=mongodb
MONGO_PORT=27017
```

### 3. تطبيق Migrations

```bash
python manage.py migrate
```

### 4. تشغيل السيرفر

```bash
python manage.py runserver 0.0.0.0:8002
```

## 📖 الاستخدام

### 1. رفع ملف كود

```bash
curl -X POST http://localhost:8002/api/codefiles/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "ProductManager.java",
    "file_type": "java",
    "content": "public class ProductManager { ... }"
  }'
```

**Response:**
```json
{
  "id": "60f7b1c8e4b0c8a2d8f9e1a2",
  "filename": "ProductManager.java",
  "file_type": "java",
  "uploaded_at": "2026-01-03T10:30:00Z",
  "analysis_status": "PENDING"
}
```

### 2. بدء التحليل

```bash
curl -X POST http://localhost:8002/api/codefiles/60f7b1c8e4b0c8a2d8f9e1a2/analyze/
```

### 3. الحصول على نتائج التحليل

```bash
curl -X GET http://localhost:8002/api/analysis-results/60f7b1c8e4b0c8a2d8f9e1a2/
```

### 4. توليد الشرح

```bash
# شرح عالي المستوى
curl -X GET "http://localhost:8002/api/ai-explanations/60f7b1c8e4b0c8a2d8f9e1a2/?type=high_level"

# شرح تقني مفصل
curl -X GET "http://localhost:8002/api/ai-explanations/60f7b1c8e4b0c8a2d8f9e1a2/?type=low_level"
```

### 5. تصدير PDF

```bash
curl -X GET "http://localhost:8002/api/export/60f7b1c8e4b0c8a2d8f9e1a2/?format=pdf&type=detailed&mode=download" \
  --output report.pdf
```

## 📚 API Documentation

### Endpoints الرئيسية

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/codefiles/` | POST | رفع ملف كود جديد |
| `/api/codefiles/{id}/analyze/` | POST | بدء تحليل الكود |
| `/api/analysis-results/{id}/` | GET | الحصول على نتائج التحليل |
| `/api/ai-explanations/{id}/` | GET | الحصول على الشرح |
| `/api/export/{id}/` | GET/POST | تصدير التوثيق |
| `/api/generated-files/` | GET | قائمة الملفات المولدة |

### معاملات التصدير

| المعامل | القيم | الافتراضي | الوصف |
|---------|-------|-----------|-------|
| `format` | `pdf`, `markdown` | `pdf` | صيغة الملف |
| `type` | `high`, `low`, `detailed` | `detailed` | نوع الشرح |
| `mode` | `display`, `download` | `display` | طريقة العرض |
| `image_url` | URL | - | رابط Class Diagram |

## 🏗️ البنية

```
Ai_project/
├── core_ai/                      # التطبيق الرئيسي
│   ├── ai_engine/               # محرك الذكاء الاصطناعي
│   │   ├── agents/             # وكلاء AI (High/Low/Verifier)
│   │   ├── doc/                # مولدات التوثيق (PDF/Markdown)
│   │   ├── llm_client.py       # عميل OpenRouter
│   │   └── orchestrator.py     # منسق العمليات
│   ├── language_processors/     # معالجات اللغات
│   │   ├── java_processor.py   # معالج Java
│   │   └── python_processor.py # معالج Python
│   ├── views/                   # API Views
│   │   ├── codefile.py         # إدارة الملفات
│   │   ├── analysis.py         # التحليل
│   │   ├── explanation_views.py # الشروحات
│   │   └── export_views.py     # التصدير
│   ├── models.py                # نماذج البيانات
│   ├── serializers.py           # Django REST Serializers
│   └── urls.py                  # URL Routing
├── Ai_project/                  # إعدادات Django
│   ├── settings.py             # الإعدادات الرئيسية
│   └── urls.py                 # URL الرئيسي
├── templates/                   # قوالب HTML
├── staticfiles/                 # ملفات ثابتة
├── manage.py                    # Django Management
├── requirements.txt             # المتطلبات
└── README.md                    # هذا الملف
```

## 🔧 التطوير

### إضافة لغة برمجة جديدة

1. أنشئ processor جديد:

```python
# core_ai/language_processors/cpp_processor.py
from .base_processor import ILanguageProcessorStrategy

class CppProcessor(ILanguageProcessorStrategy):
    def parse_code(self, code_content):
        # تحليل كود C++
        pass
    
    def extract_classes(self, ast_tree):
        # استخراج الفئات
        pass
```

2. سجل الـ processor:

```python
# core_ai/language_processors/__init__.py
from .cpp_processor import CppProcessor

processor_map = {
    'java': JavaProcessor(),
    'python': PythonProcessor(),
    'cpp': CppProcessor(),  # جديد
}
```

### إضافة نوع تصدير جديد

1. أنشئ generator جديد:

```python
# core_ai/ai_engine/doc/html.py
from .doc_generator import DocumentationGenerator

class HTMLGenerator(DocumentationGenerator):
    def _format_output(self, content, data):
        # تنسيق HTML
        pass
    
    def _export(self, formatted_html, data):
        # تصدير HTML
        pass
```

2. أضف للـ factory:

```python
# core_ai/ai_engine/doc/__init__.py
from .html import HTMLGenerator

def get_generator(format_type):
    generators = {
        'pdf': PDFGenerator,
        'markdown': MarkdownGenerator,
        'html': HTMLGenerator,  # جديد
    }
    return generators.get(format_type)()
```

### تخصيص تنسيقات PDF

عدّل ملف `core_ai/ai_engine/doc/pdf.py`:

```python
# تغيير الألوان
.class-header {
    background: linear-gradient(135deg, #your-color1, #your-color2);
}

# تغيير الخطوط
body {
    font-family: 'Your-Font', sans-serif;
}
```

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
python manage.py test

# اختبار محدد
python manage.py test core_ai.tests.test_java_processor

# مع coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 المقاييس والإحصائيات

### استخراج الخصائص

يستخرج النظام المقاييس التالية:
- عدد الأسطر (LOC)
- عدد الفئات
- عدد الطرق
- Cyclomatic Complexity
- Design Patterns المكتشفة

### التحليل الدلالي

- علاقات الوراثة (Inheritance)
- علاقات التركيب (Composition)
- علاقات الربط (Association)
- التبعيات (Dependencies)

## 🔐 الأمان

### المفاتيح المطلوبة

```bash
# في .env
AI_DJANGO_SECRET_KEY=your-strong-secret-key
OPENROUTER_API_KEY=your-api-key
AI_SERVICE_KEY=your-service-key
```

### توليد مفاتيح قوية

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### التحقق من الإعدادات

```bash
# فحص Django
python manage.py check

# فحص الأمان
python manage.py check --deploy
```

## 📝 التوثيق الإضافي

- [API_GUIDE.md](API_GUIDE.md) - دليل API الكامل
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - دليل المطورين
- [AI_SYSTEM_DOCUMENTATION.md](AI_SYSTEM_DOCUMENTATION.md) - توثيق نظام AI

## 🐛 استكشاف الأخطاء

### مشكلة: فشل التحليل

```bash
# تحقق من اللوجات
tail -f logs/ai_project.log

# تحقق من MongoDB
docker-compose logs mongodb
```

### مشكلة: فشل توليد PDF

```bash
# تحقق من WeasyPrint
pip install --upgrade weasyprint

# تحقق من المكتبات المطلوبة (Windows)
# راجع: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html
```

### مشكلة: بطء في التوليد

```bash
# استخدم Redis للتخزين المؤقت
REDIS_URL=redis://localhost:6379/0

# زد عدد Celery workers
celery -A Ai_project worker -l info --concurrency=4
```

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المشروع
2. إنشاء branch للميزة
3. Commit التغييرات
4. فتح Pull Request

## 📞 الدعم

- **Issues**: افتح issue في GitHub
- **Documentation**: راجع الملفات في `docs/`
- **Logs**: تحقق من `logs/ai_project.log`

---

**آخر تحديث:** يناير 2026  
**الإصدار:** 2.0
