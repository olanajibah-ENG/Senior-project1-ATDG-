// Translation files for English and Arabic
export const translations = {
  en: {
    // Navigation
    'nav.home': 'AutoTest & DocGen',
    'nav.projects': 'Projects',
    'nav.settings': 'Settings',
    'nav.logout': 'Log Out',
    'nav.language': 'العربية',

    // Dashboard
    'dashboard.title': 'Projects Workspace',
    'dashboard.subtitle': 'Organize your university projects and attach code artifacts.',
    'dashboard.refresh': 'Refresh',
    'dashboard.new_project': 'New project',

    // Project Modal
    'project.create_title': 'Create New Project',
    'project.create_subtitle': 'Give your project a clear name and an optional short description.',
    'project.edit_title': 'Edit Project',
    'project.edit_subtitle': 'Update the project title or description without affecting its artifacts.',
    'project.title_label': 'Title',
    'project.description_label': 'Description',
    'project.create_button': 'Create Project',
    'project.update_button': 'Update Project',
    'project.cancel': 'Cancel',
    'project.delete_title': 'Delete Project',
    'project.delete_message': 'Are you sure you want to delete this project? This action cannot be undone.',
    'project.delete_confirm': 'Delete',

    // Code Upload Modal
    'code.add_title': 'Add code to',
    'code.add_subtitle': 'Attach a Python or Java file to this project to generate a class diagram.',
    'code.name_label': 'Code Name',
    'code.name_placeholder': 'e.g. PaymentService, StudentManager',
    'code.name_hint': 'A short, meaningful name for this code unit.',
    'code.file_label': 'File Name',
    'code.file_placeholder': 'e.g. payment_service.py, StudentManager.java',
    'code.file_hint': 'Optional – we will use the uploaded file name if left empty.',
    'code.language_label': 'Language',
    'code.version_label': 'Version',
    'code.version_placeholder': 'e.g. 3.11, Java 17',
    'code.code_label': 'Code (optional if file is uploaded)',
    'code.code_placeholder': 'Paste your code here...',
    'code.code_hint': 'You can either paste the code here or upload a .py / .java file below.',
    'code.upload_label': 'Or upload file',
    'code.generate_button': 'Generate Class Diagram',
    'code.processing': 'Processing...',

    // Diagram Page
    'diagram.title': 'Class Diagram',
    'diagram.back': 'Back to Dashboard',
    'diagram.export': 'Export PNG',
    'diagram.loading': 'جاري تحضير المخطط...',

    // Analysis
    'analysis.summary': 'Static analysis completed successfully. No critical issues found.',
    'analysis.metrics': 'Metrics',

    // Alerts
    'alert.success': 'Success!',
    'alert.error': 'Error',
    'alert.project_created': 'Project created successfully!',
    'alert.project_updated': 'Project updated successfully!',
    'alert.project_deleted': 'Project deleted successfully!',

    // Validation
    'validation.required': 'This field is required.',
    'validation.title_required': 'Title is required.',
    'validation.title_length': 'Title must be 255 characters or less.',
    'validation.code_required': 'Code name is required.',
    'validation.code_or_file': 'Please provide code text or upload a file.',

    // General
    'general.username': 'Username',
    'general.loading': 'Loading...',
    'general.no_classes': 'No classes found in the uploaded code.',
    'general.no_diagram': 'No diagram data found. Please generate the diagram again from the dashboard.',
    'general.close': 'Close',
  },
  ar: {
    // Navigation
    'nav.home': 'AutoTest & DocGen',
    'nav.projects': 'المشاريع',
    'nav.settings': 'الإعدادات',
    'nav.logout': 'تسجيل الخروج',
    'nav.language': 'English',

    // Dashboard
    'dashboard.title': 'مساحة العمل للمشاريع',
    'dashboard.subtitle': 'نظم مشاريعك الجامعية وربط ملفات الكود بها.',
    'dashboard.refresh': 'تحديث',
    'dashboard.new_project': 'مشروع جديد',

    // Project Modal
    'project.create_title': 'إنشاء مشروع جديد',
    'project.create_subtitle': 'أعطِ مشروعك اسماً واضحاً ووصفاً مختصراً اختيارياً.',
    'project.edit_title': 'تعديل المشروع',
    'project.edit_subtitle': 'حدث عنوان المشروع أو الوصف دون التأثير على ملفاته.',
    'project.title_label': 'العنوان',
    'project.description_label': 'الوصف',
    'project.create_button': 'إنشاء المشروع',
    'project.update_button': 'تحديث المشروع',
    'project.cancel': 'إلغاء',
    'project.delete_title': 'حذف المشروع',
    'project.delete_message': 'هل أنت متأكد من حذف هذا المشروع؟ هذا الإجراء لا يمكن التراجع عنه.',
    'project.delete_confirm': 'حذف',

    // Code Upload Modal
    'code.add_title': 'إضافة كود إلى',
    'code.add_subtitle': 'اربط ملف Python أو Java بهذا المشروع لتوليد مخطط كلاسات.',
    'code.name_label': 'اسم الكود',
    'code.name_placeholder': 'مثال: PaymentService, StudentManager',
    'code.name_hint': 'اسم قصير ومعنوي لوحدة الكود هذه.',
    'code.file_label': 'اسم الملف',
    'code.file_placeholder': 'مثال: payment_service.py, StudentManager.java',
    'code.file_hint': 'اختياري - سنستخدم اسم الملف المرفوع إذا ترك فارغاً.',
    'code.language_label': 'اللغة',
    'code.version_label': 'الإصدار',
    'code.version_placeholder': 'مثال: 3.11, Java 17',
    'code.code_label': 'الكود (اختياري إذا تم رفع ملف)',
    'code.code_placeholder': 'الصق كودك هنا...',
    'code.code_hint': 'يمكنك لصق الكود هنا أو رفع ملف .py / .java أدناه.',
    'code.upload_label': 'أو رفع ملف',
    'code.generate_button': 'توليد مخطط الكلاسات',
    'code.processing': 'جاري المعالجة...',

    // Diagram Page
    'diagram.title': 'مخطط الكلاسات',
    'diagram.back': 'العودة إلى لوحة التحكم',
    'diagram.export': 'تصدير PNG',
    'diagram.loading': 'جاري تحضير المخطط...',

    // Analysis
    'analysis.summary': 'اكتمل التحليل الثابت بنجاح. لم يتم العثور على مشاكل حرجة.',
    'analysis.metrics': 'المقاييس',

    // Alerts
    'alert.success': 'نجح!',
    'alert.error': 'خطأ',
    'alert.project_created': 'تم إنشاء المشروع بنجاح!',
    'alert.project_updated': 'تم تحديث المشروع بنجاح!',
    'alert.project_deleted': 'تم حذف المشروع بنجاح!',

    // Validation
    'validation.required': 'هذا الحقل مطلوب.',
    'validation.title_required': 'العنوان مطلوب.',
    'validation.title_length': 'يجب أن يكون العنوان 255 حرفاً أو أقل.',
    'validation.code_required': 'اسم الكود مطلوب.',
    'validation.code_or_file': 'يرجى تقديم نص الكود أو رفع ملف.',

    // General
    'general.username': 'اسم المستخدم',
    'general.loading': 'جاري التحميل...',
    'general.no_classes': 'لم يتم العثور على كلاسات في الكود المرفوع.',
    'general.no_diagram': 'لم يتم العثور على بيانات المخطط. يرجى توليد المخطط مرة أخرى من لوحة التحكم.',
    'general.close': 'إغلاق',
  }
};

export type Language = 'en' | 'ar';
export type TranslationKey = keyof typeof translations.en;