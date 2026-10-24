# 🤖 ai_engine - محرك الذكاء الاصطناعي

محرك الذكاء الاصطناعي الأساسي المسؤول عن التفاعل مع نماذج AI المجانية وإنتاج التوثيق التقني.

## 📁 هيكل المجلد

```
ai_engine/
├── __init__.py              # تهيئة المحرك
├── llm_client.py            # 🔗 عميل OpenRouter API
├── orchestrator.py          # 🎯 مدير العمليات والتنسيق
└── doc/                     # 📄 معالجات التوثيق والتصدير
    ├── __init__.py
    ├── doc_generator.py     # 🏭 المولد الأساسي للتوثيق
    ├── pdf.py               # 📕 مولد ملفات PDF
    └── markdown.py          # 📝 مولد ملفات Markdown
```

## 🎯 المكونات الرئيسية

### 🔗 llm_client.py - عميل OpenRouter API

**الوظائف الأساسية:**
- الاتصال بنماذج AI مجانية متطورة
- إدارة Rate Limiting ذكية
- Cache لتوفير الطلبات
- معالجة الأخطاء والاسترداد

```python
from core_ai.ai_engine.llm_client import ImprovedGeminiClient

# النماذج المتاحة المجانية
models = ImprovedGeminiClient.get_available_free_models()
for model in models:
    print(f"{model['name']}: {model['description']}")

# اختبار الاتصال
result = ImprovedGeminiClient.test_model_connection()
print("Connection Status:", result['status'])

# إرسال طلب للنموذج
response = ImprovedGeminiClient.call_gemini(
    system_prompt="أنت مساعد برمجة خبير في Java",
    user_prompt="اشرح كيفية عمل OOP في Java مع أمثلة",
    model="meta-llama/llama-3.2-3b-instruct:free"  # النموذج الافتراضي
)
```

**ميزات متقدمة:**
- **Rate Limiting**: حماية من تجاوز الحدود اليومية (200 طلب)
- **Cache ذكي**: حفظ الاستجابات لمدة 48 ساعة
- **Retry Logic**: إعادة المحاولة التلقائية عند فشل الطلبات
- **Fallback Models**: التبديل التلقائي لنماذج بديلة

### 🎯 orchestrator.py - مدير العمليات

**مسؤوليات:**
- تنسيق عمليات التحليل بين المكونات
- إدارة سير العمل من التحليل إلى التوثيق
- معالجة الأخطاء وإعادة المحاولات

```python
from core_ai.ai_engine.orchestrator import AIAnalysisOrchestrator

orchestrator = AIAnalysisOrchestrator()

# تحليل كود وإنشاء شرح شامل
result = orchestrator.analyze_and_explain(
    code_content="""
    public class Student {
        private String name;
        private int age;

        public Student(String name, int age) {
            this.name = name;
            this.age = age;
        }

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
    }
    """,
    language="java",
    explanation_type="low_level"
)

print("Analysis Result:", result['status'])
print("Explanation:", result['explanation'][:200] + "...")
```

### 📄 doc/ - معالجات التوثيق

#### 🏭 doc_generator.py - المولد الأساسي

**الكلاس الأساسي لجميع مولدات التوثيق:**
```python
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator

class CustomGenerator(DocumentationGenerator):
    def _format_output(self, content, data):
        # تخصيص تنسيق الإخراج
        return self._prepare_for_rendering(content)
```

#### 📕 pdf.py - مولد PDF المتطور

**الميزات الخاصة:**
- استخراج اسم الملف الأصلي من قاعدة البيانات
- تنسيقات PDF احترافية مع ألوان وخطوط جميلة
- جداول منظمة للميثودات والحقول
- كود ملون بـ syntax highlighting
- تذييل احترافي مع معلومات النظام

```python
from core_ai.ai_engine.doc.pdf import PDFGenerator

generator = PDFGenerator()

# إنشاء PDF مع البيانات الكاملة
pdf_bytes = generator.generate({
    'content': 'شرح مفصل للكود...',
    'analysis_id': '507f1f77bcf86cd799439011',  # سيتم استخراج اسم الملف منه
    'explanation_type': 'low_level',
    'code_content': 'public class Student { ... }'  # الكود الأصلي
})

# حفظ الملف
with open('student_analysis.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

**ما يظهر في PDF النهائي:**
- ✅ اسم الملف الصحيح: `Student.java`
- ✅ شرح مفصل من المستوى المنخفض
- ✅ جدول الميثودات والحقول
- ✅ الكود الأصلي ملون
- ✅ إحصائيات وتحليلات

#### 📝 markdown.py - مولد Markdown

**للتصدير بتنسيق Markdown:**
```python
from core_ai.ai_engine.doc.markdown import MarkdownGenerator

generator = MarkdownGenerator()
markdown_content = generator.generate({
    'content': 'شرح الكود...',
    'analysis_id': '507f1f77bcf86cd799439011'
})

with open('analysis.md', 'w', encoding='utf-8') as f:
    f.write(markdown_content)
```

## 🔧 كيفية عمل النظام

### 1. **تلقي طلب التحليل**
```
User Request → Orchestrator → LLM Client
```

### 2. **معالجة الطلب**
```
Code Analysis → AI Explanation → Document Generation
```

### 3. **إنتاج النتيجة**
```
Raw Content → Format → PDF/Markdown → Final Output
```

## ⚙️ الإعدادات والتخصيص

### 🔧 تخصيص النموذج الافتراضي
```python
# في llm_client.py
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free"

# أو استخدام نموذج محدد لمهمة معينة
response = ImprovedGeminiClient.call_gemini(
    "system prompt",
    "user prompt",
    model="mistralai/mistral-small-3.1-24b-instruct:free"
)
```

### 🎨 تخصيص تنسيق PDF
```python
# في pdf.py - دالة _format_output
def _format_output(self, content, data):
    # تخصيص الألوان والخطوط
    css_styles = """
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .method-table { border-collapse: collapse; }
    /* المزيد من التنسيقات المخصصة */
    """
    # ...
```

### 📊 تخصيص إحصائيات التحليل
```python
# إضافة إحصائيات مخصصة في _format_output
stats_html = f"""
<div class="stats-box">
    <div class="stats-number">{data.get('methods_count', 0)}</div>
    <div class="stats-label">Methods</div>
</div>
<div class="stats-box">
    <div class="stats-number">{data.get('classes_count', 0)}</div>
    <div class="stats-label">Classes</div>
</div>
"""
```

## 📊 الأداء والإحصائيات

### 🤖 مقارنة النماذج

| النموذج | السرعة | الدقة | السياق | الحالة |
|---------|--------|-------|--------|--------|
| **Llama 3.2** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4K | **افتراضي** |
| **Mistral Small** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 32K | متاح |
| **Gemma 7B** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 8K | متاح |

### ⚡ مقاييس الأداء
- **استجابة AI**: 2-5 ثواني
- **معالجة PDF**: < 3 ثواني
- **حجم PDF**: 50KB - 2MB
- **معدل النجاح**: > 95%

## 🔧 استكشاف الأخطاء

### ❌ مشاكل شائعة وحلولها:

#### 1. **خطأ في الاتصال بـ API**
```python
# فحص API Key
import os
api_key = os.getenv('OPENROUTER_API_KEY')
print("API Key:", "موجود" if api_key else "مفقود")

# اختبار الاتصال
from core_ai.ai_engine.llm_client import ImprovedGeminiClient
result = ImprovedGeminiClient.test_model_connection()
print("Connection:", result)
```

#### 2. **خطأ في توليد PDF**
```python
# فحص WeasyPrint
try:
    import weasyprint
    print("WeasyPrint: مثبت")
except ImportError:
    print("WeasyPrint: غير مثبت - قم بتشغيل: pip install weasyprint")
```

#### 3. **خطأ في استخراج اسم الملف**
```python
# فحص قاعدة البيانات
from core_ai.mongo_utils import get_mongo_db
from bson import ObjectId

db = get_mongo_db()
analysis = db.analysis_results.find_one({"_id": ObjectId("analysis_id")})
if analysis:
    code_file = db.code_files.find_one({"_id": analysis.get("code_file_id")})
    print("Original filename:", code_file.get("filename") if code_file else "Not found")
```

## 📚 الوثائق ذات الصلة

- `../../../FREE_MODELS_GUIDE.md` - دليل النماذج المجانية
- `../../../AI_SYSTEM_DOCUMENTATION.md` - شرح مفصل للنظام
- `doc/README.md` - دليل معالجات التوثيق

## 🚀 التطوير المستقبلي

### خطط محتملة:
- ✅ دعم نماذج محلية (Ollama)
- ✅ تحسين خوارزمية اختيار النموذج التلقائي
- ✅ إضافة المزيد من تنسيقات التصدير
- ✅ دعم اللغات البرمجية الإضافية

---

**هذا هو قلب محرك الذكاء الاصطناعي - المسؤول عن إنتاج التوثيق الذكي 🚀**
