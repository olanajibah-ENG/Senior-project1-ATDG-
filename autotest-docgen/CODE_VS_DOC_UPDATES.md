# CodeVsDoc Component - Complete English Translation & Color Updates

## Text Replacements Needed:

### Step Labels
```tsx
// OLD
const stepLabels = ['المشروع', 'الملف', 'اختيار', 'تحليل', 'النتائج'];

// NEW
const stepLabels = ['Project', 'File', 'Select', 'Analyzing', 'Results'];
```

### Project Step
```tsx
// OLD
<p className="cvd-section-label">اختر المشروع</p>
<span>جارٍ تحميل المشاريع...</span>
<p className="cvd-empty-note">لا توجد مشاريع.</p>
<button>التالي — اختر ملف</button>

// NEW
<p className="cvd-section-label">Select Project</p>
<span>Loading projects...</span>
<p className="cvd-empty-note">No projects found.</p>
<button>Next — Select File</button>
```

### File Step
```tsx
// OLD
<p className="cvd-section-label">اختر ملف الكود</p>
<span>جارٍ تحميل الملفات...</span>
<p className="cvd-empty-note">لا توجد ملفات لهذا المشروع.</p>
{f.has_documentation ? 'موثق' : 'غير موثق'}
<button>← رجوع</button>
<button>التالي — اختر نسخة وتوثيق</button>

// NEW
<p className="cvd-section-label">Select Code File</p>
<span>Loading files...</span>
<p className="cvd-empty-note">No files found for this project.</p>
{f.has_documentation ? 'Documented' : 'Not Documented'}
<button>← Back</button>
<button>Next — Select Version & Doc</button>
```

### Select Step
```tsx
// OLD
<span>نسخة الكود</span>
<span>تحميل النسخ...</span>
<p className="cvd-empty-note">لا توجد نسخ لهذا الملف.</p>
<span>التوثيق المرتبط</span>
<span>تحميل التوثيق...</span>
<p className="cvd-empty-note">لا يوجد توثيق لهذا الملف.</p>
<p className="cvd-auto-note">جُلب تلقائياً بناءً على الملف المختار</p>
<button>← رجوع</button>
<button>بدء التحليل</button>

// NEW
<span>Code Version</span>
<span>Loading versions...</span>
<p className="cvd-empty-note">No versions found for this file.</p>
<span>Linked Documentation</span>
<span>Loading documentation...</span>
<p className="cvd-empty-note">No documentation found for this file.</p>
<p className="cvd-auto-note">Auto-fetched based on selected file</p>
<button>← Back</button>
<button>Start Analysis</button>
```

### Analyzing Step
```tsx
// OLD
<h3>جارٍ التحليل...</h3>
['بدء التحليل', 'مقارنة الكود بالتوثيق', 'تحليل الدلالات', 'معالجة التناقضات', 'جلب النتائج']

// NEW
<h3>Analyzing...</h3>
['Starting Analysis', 'Comparing Code & Docs', 'Semantic Analysis', 'Processing Conflicts', 'Fetching Results']
```

### Result Step
```tsx
// OLD
<div className="lbl">تناقضات</div>
<div className="lbl">توافق</div>
<div className="lbl">الدرجة</div>
{t === 'summary' ? 'التناقضات' : t === 'coverage' ? 'Coverage Map' : 'AI اقتراحات'}
<p className="cvd-empty-note">لا توجد تناقضات.</p>
{ l: 'عناصر محللة', ... }
{ l: 'موثقة كاملاً', ... }
{ l: 'موثقة جزئياً', ... }
{ l: 'غير موثقة', ... }
<p>عناصر غير موثقة</p>
<p>تفاصيل التوثيق</p>
<p className="cvd-empty-note">لا توجد اقتراحات.</p>
<button>← تحليل جديد</button>
<button>تصدير PDF</button>

// NEW
<div className="lbl">Conflicts</div>
<div className="lbl">Compatibility</div>
<div className="lbl">Grade</div>
{t === 'summary' ? 'Conflicts' : t === 'coverage' ? 'Coverage Map' : 'AI Suggestions'}
<p className="cvd-empty-note">No conflicts found.</p>
{ l: 'Elements Analyzed', ... }
{ l: 'Fully Documented', ... }
{ l: 'Partially Documented', ... }
{ l: 'Undocumented', ... }
<p>Undocumented Elements</p>
<p>Documentation Details</p>
<p className="cvd-empty-note">No suggestions found.</p>
<button>← New Analysis</button>
<button>Export PDF</button>
```

### ConflictCard Labels
```tsx
// OLD
<div className="cvd-ba-label">قبل</div>
<div className="cvd-ba-label">بعد</div>

// NEW
<div className="cvd-ba-label">Before</div>
<div className="cvd-ba-label">After</div>
```

## CSS Color Updates for Light Mode:

```css
/* File Selection - Make text darker and more visible */
.dashboard.light .cvd-fname {
  color: #1e1b4b !important;
  font-weight: 700 !important;
  font-size: 15px !important;
}

.dashboard.light .cvd-fpath {
  color: #7c3aed !important;
  font-size: 13px !important;
}

/* Version Selection - Darker text */
.dashboard.light .cvd-ver-num {
  color: #1e1b4b !important;
  font-weight: 700 !important;
  font-size: 15px !important;
}

.dashboard.light .cvd-ver-date {
  color: #7c3aed !important;
  font-size: 13px !important;
}

/* Doc Selection - Darker text */
.dashboard.light .cvd-doc-name {
  color: #1e1b4b !important;
  font-weight: 700 !important;
  font-size: 15px !important;
}

.dashboard.light .cvd-doc-path {
  color: #7c3aed !important;
  font-size: 13px !important;
}

/* Panel Headers */
.dashboard.light .cvd-panel-header {
  background: rgba(139,92,246,0.12) !important;
  border-bottom-color: rgba(139,92,246,0.25) !important;
  color: #1e1b4b !important;
  font-weight: 700 !important;
}

/* Selection Glow Animation */
.cvd-file-row.selected,
.cvd-ver-row.sel-a,
.cvd-doc-row.selected {
  animation: selectionGlow 0.5s ease-out;
  box-shadow: 0 0 20px rgba(139,92,246,0.4), 
              inset 0 0 10px rgba(139,92,246,0.1);
}

@keyframes selectionGlow {
  0% {
    box-shadow: 0 0 0 rgba(139,92,246,0);
  }
  50% {
    box-shadow: 0 0 30px rgba(139,92,246,0.6),
                inset 0 0 15px rgba(139,92,246,0.2);
  }
  100% {
    box-shadow: 0 0 20px rgba(139,92,246,0.4),
                inset 0 0 10px rgba(139,92,246,0.1);
  }
}
```

## Implementation Steps:

1. Replace all Arabic text with English equivalents
2. Update CSS for darker, more visible colors in light mode
3. Add selection glow animation
4. Update analyzing step with emoji indicators
5. Ensure all labels are properly translated
