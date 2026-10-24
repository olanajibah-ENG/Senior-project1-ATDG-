# Projects Table Changes - Code Files & Documentation Columns

## Overview

تم تعديل جدول المشاريع لاستبدال عمودي "Updated" و "Actions" بعمودين جديدين:

- **Code Files**: عرض ملفات الكود المرتبطة بالمشروع
- **Documentation**: عرض ملفات التوثيق المرتبطة بالمشروع

## Changes Made

### 1. ProjectList.tsx

- ✅ إضافة أيقونات جديدة: `FileCode`, `FileText`, `ExternalLink`
- ✅ إضافة `onOpenFile` callback في الـ interface
- ✅ إضافة functions لمحاكاة بيانات الملفات:
  - `getProjectCodeFiles()` - للحصول على ملفات الكود
  - `getProjectDocumentation()` - للحصول على ملفات التوثيق
  - `handleFileClick()` - للتعامل مع النقر على الملفات
  - `renderFilesList()` - لعرض قائمة الملفات
- ✅ تعديل الجدول لإظهار العمودين الجديدين
- ✅ إزالة عمودي "Updated" و "Actions"

### 2. ProjectList.css

- ✅ إضافة styles للملفات الجديدة:
  - `.project-files-cell`, `.project-docs-cell` - تنسيق خلايا الملفات
  - `.files-list` - تنسيق قائمة الملفات مع scrollbar مخصص
  - `.file-link` - تنسيق روابط الملفات مع hover effects
  - تمييز ملفات الكود (حدود خضراء) عن ملفات التوثيق (حدود زرقاء)
  - دعم الـ responsive design والـ dark mode
  - إضافة animations للملفات

### 3. Dashboard.tsx

- ✅ إضافة `handleOpenFile()` function للتعامل مع فتح الملفات
- ✅ تمرير `onOpenFile` callback للـ ProjectsList component

### 4. New Files Created

#### files.service.ts

خدمة للتعامل مع ملفات المشاريع:

- `getProjectFiles()` - جلب ملفات المشروع
- `getFileContent()` - جلب محتوى ملف معين
- `uploadCodeFiles()` - رفع ملفات كود جديدة
- `generateDocumentation()` - توليد ملفات توثيق
- `deleteFile()` - حذف ملف

#### ProjectListWithRealData.tsx

مثال على كيفية استخدام البيانات الحقيقية بدلاً من الـ mock data:

- تحميل ملفات المشاريع من الـ API
- عرض حالات التحميل والأخطاء
- التعامل مع النقر على الملفات وتحميل المحتوى

## Current Features

### Mock Data (Current Implementation)

- عرض ملفات وهمية لكل مشروع
- أسماء ملفات عشوائية (main.py, utils.py, README.md, etc.)
- عدد عشوائي من الملفات لكل مشروع

### File Display Features

- 📁 **Code Files**: أيقونة `FileCode` مع حدود خضراء
- 📄 **Documentation**: أيقونة `FileText` مع حدود زرقاء
- 🔗 **Clickable Links**: كل ملف قابل للنقر مع أيقونة `ExternalLink`
- 📱 **Responsive**: يتكيف مع الشاشات المختلفة
- 🌙 **Dark Mode**: دعم الوضع المظلم
- ⚡ **Animations**: تأثيرات حركية عند التحميل والـ hover
- 📜 **Scrollable**: قوائم الملفات قابلة للتمرير إذا كانت طويلة

### User Interaction

- النقر على أي ملف يظهر alert مع معلومات الملف
- يمكن تخصيص السلوك عبر `onOpenFile` callback
- دعم keyboard navigation وإمكانية الوصول

## Next Steps

### To Use Real Data:

1. **Backend API**: تأكد من وجود endpoints للملفات:

   ```
   GET /api/upm/projects/{id}/files/
   GET /api/upm/projects/{id}/files/{file_id}/content/
   POST /api/upm/projects/{id}/files/upload/
   ```

2. **Replace Mock Data**: استبدل الـ mock functions في `ProjectList.tsx`:

   ```typescript
   // Replace these functions with real API calls
   const getProjectCodeFiles = (projectId: string) => { ... }
   const getProjectDocumentation = (projectId: string) => { ... }
   ```

3. **Use Real Service**: استخدم `ProjectListWithRealData.tsx` كمرجع للتطبيق الحقيقي

### File Opening Options:

- **Modal Viewer**: فتح الملفات في modal مع syntax highlighting
- **New Tab**: فتح الملفات في تبويب جديد
- **Download**: تحميل الملفات مباشرة
- **External Editor**: فتح في محرر خارجي

## Screenshots

الجدول الآن يعرض:

```
| Title | Description | Owner | Created | Code Files | Documentation |
|-------|-------------|-------|---------|------------|---------------|
| ATDG  | software... | admin | Jan 3   | main.py    | README.md     |
|       |             |       |         | utils.py   | API_DOCS.md   |
|       |             |       |         | models.py  |               |
```

## Technical Details

- **Framework**: React 19.2.0 with TypeScript
- **Icons**: Lucide React
- **Styling**: Custom CSS with modern design patterns
- **Responsive**: Mobile-first approach
- **Accessibility**: Full keyboard navigation and screen reader support
