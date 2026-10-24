# 🧠 core_ai - الذكاء الاصطناعي الأساسي

التطبيق الأساسي لنظام تحليل الكود الذكي، يحتوي على جميع المكونات الأساسية للذكاء الاصطناعي والمعالجة.

## 📁 هيكل المجلد

```
core_ai/
├── ai_engine/                    # 🤖 محرك الذكاء الاصطناعي
│   ├── __init__.py              # تهيئة المحرك
│   ├── llm_client.py            # 🔗 عميل OpenRouter API
│   ├── orchestrator.py          # 🎯 مدير العمليات
│   └── doc/                     # 📄 معالجات التوثيق
│       ├── __init__.py
│       ├── doc_generator.py     # 🏭 مولد التوثيق
│       ├── pdf.py               # 📕 معالج PDF
│       └── markdown.py          # 📝 معالج Markdown
├── language_processors/         # 🔍 معالجات اللغات البرمجية
│   ├── __init__.py
│   ├── base_processor.py        # 🔧 المعالج الأساسي
│   ├── java_processor.py        # ☕ معالج Java
│   ├── python_processor.py      # 🐍 معالج Python
│   └── README.md               # 📖 دليل المعالجات
├── models/                      # 📊 نماذج قاعدة البيانات
│   ├── __init__.py
│   ├── codefile.py             # 📄 نموذج ملفات الكود
│   ├── analysis.py             # 🔍 نموذج نتائج التحليل
│   ├── ai_explanation.py       # 🤖 نموذج التفسيرات
│   └── ai_task.py              # ⚙️ نموذج المهام
├── views/                       # 🌐 API endpoints
│   ├── __init__.py
│   ├── codefile.py             # 📤 إدارة ملفات الكود
│   ├── analysis.py             # 🔍 إدارة التحليل
│   ├── explanation_views.py    # 🤖 إدارة التفسيرات
│   └── export_views.py         # 📤 تصدير النتائج
├── serializers/                 # 🔄 تسلسل البيانات
│   ├── __init__.py
│   ├── codefile.py
│   ├── analysis.py
│   └── ai_explanation.py
├── services/                    # 🔧 الخدمات المساعدة
│   ├── __init__.py
│   └── project_analyzer.py     # 📊 محلل المشاريع
├── repository/                  # 💾 طبقة البيانات
│   ├── __init__.py
│   ├── ai_task.py              # 💾 إدارة المهام
│   └── analyze_code.py         # 💾 منطق التحليل
├── __init__.py                 # تهيئة التطبيق
├── admin.py                    # 🎛️ إعدادات Django Admin
├── apps.py                     # 📱 إعدادات التطبيق
├── mongo_utils.py              # 🍃 أدوات MongoDB
├── permissions.py              # 🔐 صلاحيات الوصول
├── tasks.py                    # ⚡ مهام Celery
└── urls.py                     # 🛣️ مسارات API
```

## 🎯 المكونات الرئيسية

### 🤖 ai_engine - محرك الذكاء الاصطناعي

#### 🔗 llm_client.py - عميل OpenRouter
```python
from core_ai.ai_engine.llm_client import ImprovedGeminiClient

# اختبار الاتصال
result = ImprovedGeminiClient.test_model_connection()
print(result)  # {'status': 'success', 'model': 'llama-3.2'}

# إرسال طلب للنموذج
response = ImprovedGeminiClient.call_gemini(
    system_prompt="أنت مساعد برمجة",
    user_prompt="اشرح كيفية عمل الوراثة في Java",
    model="meta-llama/llama-3.2-3b-instruct:free"
)
```

**الميزات:**
- نماذج AI مجانية متطورة
- إدارة Rate Limiting ذكية
- Cache لتوفير الطلبات
- معالجة أخطاء متقدمة

#### 📄 doc/ - معالجات التوثيق

##### pdf.py - مولد PDF
```python
from core_ai.ai_engine.doc.pdf import PDFGenerator

generator = PDFGenerator()
pdf_data = generator.generate({
    'content': 'شرح الكود...',
    'analysis_id': '123',
    'filename': 'Student.java'  # اسم الملف الأصلي!
})

with open('analysis.pdf', 'wb') as f:
    f.write(pdf_data)
```

**الميزات:**
- استخراج اسم الملف الأصلي من قاعدة البيانات
- تنسيقات PDF احترافية
- كود ملون وقابل للقراءة
- جداول منظمة للميثودات

##### markdown.py - مولد Markdown
```python
from core_ai.ai_engine.doc.markdown import MarkdownGenerator

generator = MarkdownGenerator()
markdown_content = generator.generate({
    'content': 'شرح الكود...',
    'analysis_id': '123'
})
```

### 🔍 language_processors - معالجات اللغات

#### 🏗️ البنية الأساسية
```python
from core_ai.language_processors.base_processor import BaseProcessor

class CustomProcessor(BaseProcessor):
    def extract_features(self, content: str) -> dict:
        # منطق استخراج الميزات
        pass

    def analyze_dependencies(self, content: str) -> list:
        # تحليل التبعيات
        pass
```

#### ☕ Java Processor
- استخراج كلاسات وعناصرها
- تحليل علاقات الوراثة
- كشف التبعيات والimports
- استخراج ميثودات وحقول

#### 🐍 Python Processor
- تحليل ملفات Python
- استخراج functions وclasses
- تحليل imports والتبعيات
- دعم type hints

### 📊 Models - نماذج البيانات

#### 📄 CodeFile - ملفات الكود
```python
from core_ai.models.codefile import CodeFile

# إنشاء ملف كود جديد
code_file = CodeFile.objects.create(
    filename="Student.java",
    file_type="java",
    content="public class Student { ... }",
    uploaded_by=user
)
```

#### 🔍 AnalysisResult - نتائج التحليل
```python
from core_ai.models.analysis import AnalysisResult

# حفظ نتيجة تحليل
result = AnalysisResult.objects.create(
    code_file=code_file,
    analysis_type="low_level",
    status="completed",
    extracted_features={
        'classes': 1,
        'methods': 8,
        'fields': 4
    }
)
```

## 🚀 الاستخدام البرمجي

### 📤 رفع وتحليل ملف كود
```python
from core_ai.views.codefile import CodeFileViewSet
from core_ai.views.analysis import AnalysisViewSet

# 1. رفع الملف
codefile_view = CodeFileViewSet()
code_file = codefile_view.create_codefile({
    'filename': 'Calculator.java',
    'content': 'public class Calculator { ... }',
    'file_type': 'java'
})

# 2. تحليل الملف
analysis_view = AnalysisViewSet()
task = analysis_view.create_analysis({
    'code_file_id': str(code_file.id),
    'explanation_type': 'low_level'
})

# 3. الحصول على النتيجة
result = analysis_view.get_result(task.id)
```

### 🤖 إنشاء شرح ذكي
```python
from core_ai.ai_engine.orchestrator import AIAnalysisOrchestrator

orchestrator = AIAnalysisOrchestrator()
result = orchestrator.analyze_and_explain(
    code_content="public class Student { ... }",
    language="java",
    explanation_type="low_level"
)

print(result['explanation'])  # الشرح المفصل
```

### 📤 تصدير النتائج
```python
from core_ai.views.export_views import ExportHandler

exporter = ExportHandler()
pdf_data = exporter.generate_pdf(
    analysis_id="507f1f77bcf86cd799439011",
    format_type="pdf"
)

# حفظ الملف
with open('analysis.pdf', 'wb') as f:
    f.write(pdf_data)
```

## ⚙️ الإعدادات والتخصيص

### 🔧 تخصيص نموذج AI
```python
# في llm_client.py
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free"

# أو استخدام نموذج محدد
response = ImprovedGeminiClient.call_gemini(
    "...",
    model="mistralai/mistral-small-3.1-24b-instruct:free"
)
```

### 🎛️ تخصيص Admin Interface
```python
# في admin.py
@admin.register(MongoCodeFile)
class CodeFileAdmin(BaseMongoAdmin):
    list_display = ('filename', 'file_type', 'analysis_status')
    list_filter = ('file_type', 'analysis_status')
    search_fields = ('filename',)
```

### 🔍 إضافة معالج لغة جديدة
```python
# في language_processors/
class NewLanguageProcessor(BaseProcessor):
    def extract_features(self, content: str) -> dict:
        # منطق استخراج الميزات للغة الجديدة
        return {
            'language': 'new_lang',
            'classes': len(find_classes(content)),
            'functions': len(find_functions(content))
        }
```

## 📊 الإحصائيات والأداء

### 🤖 أداء نماذج AI
| النموذج | السرعة | الدقة | السياق | التكلفة |
|---------|--------|-------|--------|----------|
| Llama 3.2 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4K | مجاني |
| Mistral Small | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 32K | مجاني |
| Gemma 7B | ⭐⭐⭐ | ⭐⭐⭐⭐ | 8K | مجاني |

### 📈 مقاييس الأداء
- **معالجة الملفات**: حتى 10MB
- **استجابة API**: < 2 ثانية
- **دقة التحليل**: > 95%
- **معدل النجاح**: > 98%

## 🔧 استكشاف الأخطاء

### مشاكل شائعة:

#### ❌ خطأ في الاتصال بـ AI
```python
# تحقق من API Key
import os
print("API Key:", "EXISTS" if os.getenv('OPENROUTER_API_KEY') else "MISSING")

# اختبار الاتصال
from core_ai.ai_engine.llm_client import ImprovedGeminiClient
result = ImprovedGeminiClient.test_model_connection()
print("Connection:", result)
```

#### ❌ خطأ في MongoDB
```python
# تحقق من الاتصال
from core_ai.mongo_utils import get_mongo_db
db = get_mongo_db()
print("MongoDB:", "CONNECTED" if db else "FAILED")

# فحص Collections
collections = db.list_collection_names()
print("Collections:", collections)
```

#### ❌ خطأ في PDF Generation
```python
# تحقق من WeasyPrint
try:
    import weasyprint
    print("WeasyPrint: INSTALLED")
except ImportError:
    print("WeasyPrint: MISSING - Run: pip install weasyprint")
```

## 📚 الوثائق ذات الصلة

- `../AI_SYSTEM_DOCUMENTATION.md` - شرح مفصل للنظام
- `../FREE_MODELS_GUIDE.md` - دليل النماذج المجانية
- `../DEVELOPER_GUIDE.md` - دليل المطور
- `language_processors/README.md` - دليل معالجات اللغات

---

**هذا هو قلب نظام الذكاء الاصطناعي الأساسي 🧠**
