# مثال على استخدام واجهة Conflict Detection المحدثة

## 🎯 كيفية الاستخدام

### 1. استيراد المكون

```tsx
import SimpleConflictSelector from './compoents/ConflictDetection/ConflictTypeSelector/SimpleConflictSelector';
import type { ConflictType } from './compoents/ConflictDetection/ConflictTypeSelector/ConflictTypeSelector';
```

### 2. استخدام المكون في التطبيق

```tsx
function App() {
  const handleConflictTypeSelect = (type: ConflictType) => {
    console.log('Selected conflict type:', type);
    // يمكنك هنا فتح الواجهة المناسبة حسب النوع المختار
    switch(type) {
      case 'code_vs_code':
        // فتح واجهة Code vs Code
        break;
      case 'code_vs_doc':
        // فتح واجهة Code vs Documentation
        break;
      case 'full_analysis':
        // فتح واجهة Full Analysis
        break;
    }
  };

  return (
    <div className="app">
      <SimpleConflictSelector onSelect={handleConflictTypeSelect} />
    </div>
  );
}
```

### 3. دعم الوضع الداكن

```tsx
function App() {
  const [isDark, setIsDark] = useState(true);

  return (
    <div className={isDark ? 'dark' : ''}>
      <SimpleConflictSelector onSelect={handleConflictTypeSelect} />
    </div>
  );
}
```

---

## 🎨 التخصيص

### تغيير الألوان

يمكنك تخصيص الألوان من خلال تعديل ملف CSS:

```css
/* تغيير لون البطاقة الموصى بها */
.scs-card.recommended {
  border-color: rgba(YOUR_COLOR_HERE);
}

/* تغيير لون العنوان */
.scs-main-title {
  background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
}
```

### تعطيل الأنيميشن

إذا كنت تريد تعطيل الأنيميشن لأسباب الأداء:

```css
/* إضافة هذا في نهاية ملف CSS */
* {
  animation: none !important;
  transition: none !important;
}
```

### تغيير سرعة الأنيميشن

```css
/* تسريع الأنيميشن */
.scs-bg-float {
  animation-duration: 15s; /* بدلاً من 25s */
}

/* تبطيء الأنيميشن */
.scs-title-shimmer {
  animation-duration: 6s; /* بدلاً من 4s */
}
```

---

## 📱 الاستجابة للشاشات

الواجهة تستجيب تلقائياً لجميع أحجام الشاشات:

- **Desktop (> 700px)**: 3 بطاقات في صف واحد
- **Mobile (< 700px)**: بطاقة واحدة في كل صف

---

## ♿ إمكانية الوصول

الواجهة تدعم:
- التنقل بلوحة المفاتيح (Tab)
- تحديد واضح عند التركيز (Focus)
- ألوان متباينة للقراءة السهلة
- أحجام نصوص مناسبة

---

## 🔧 استكشاف الأخطاء

### المشكلة: الأنيميشن لا تعمل
**الحل**: تأكد من استيراد ملف CSS:
```tsx
import './SimpleConflictSelector.css';
```

### المشكلة: الألوان لا تظهر بشكل صحيح
**الحل**: تأكد من أن المكون داخل عنصر له class `dark` للوضع الداكن

### المشكلة: البطاقات لا تستجيب للنقر
**الحل**: تأكد من تمرير دالة `onSelect` بشكل صحيح

---

## 🎬 معاينة التأثيرات

### عند تحميل الصفحة:
1. ظهور الخلفية المتحركة
2. انزلاق العنوان من الأعلى
3. ظهور Legend مع تأثير اللمعان
4. دخول البطاقات بشكل متدرج

### عند التمرير على البطاقة:
1. ارتفاع البطاقة مع تكبير خفيف
2. دوران وتكبير الأيقونة
3. ظهور تأثير الضوء الدوار
4. حركة الشارات للأعلى
5. توهج الزر

### عند النقر على الزر:
1. تأثير الموجة (Ripple)
2. تصغير خفيف
3. استدعاء دالة onSelect

---

## 📊 الأداء

- جميع الأنيميشن تستخدم `transform` و `opacity` للأداء الأمثل
- استخدام `will-change` للعناصر المتحركة
- لا توجد إعادة رسم (Repaints) غير ضرورية
- الأنيميشن سلسة على 60 FPS

---

## 🌐 التوافق

الواجهة متوافقة مع:
- ✅ Chrome (آخر إصدارين)
- ✅ Firefox (آخر إصدارين)
- ✅ Safari (آخر إصدارين)
- ✅ Edge (آخر إصدارين)
- ✅ Mobile browsers

---

## 💡 نصائح للتطوير

1. **استخدم المكون كما هو**: المكون جاهز للاستخدام مباشرة
2. **لا تعدل الأنيميشن بشكل عشوائي**: التوقيتات محسوبة بعناية
3. **اختبر على أجهزة مختلفة**: تأكد من الأداء على الأجهزة الضعيفة
4. **احتفظ بنسخة احتياطية**: قبل أي تعديلات كبيرة

---

تم إنشاء هذا الدليل لمساعدتك في استخدام الواجهة المحدثة بشكل فعال! 🚀
