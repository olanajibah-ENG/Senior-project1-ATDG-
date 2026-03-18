// Enhanced i18n implementation with comprehensive translations
export type Language = 'en' | 'ar';

export interface Translations {
  [key: string]: {
    en: string;
    ar: string;
  };
}

export interface TranslationParams {
  [key: string]: any;
}

const translations: Translations = {
  // Navigation
  'nav.home': {
    en: 'Home',
    ar: 'الرئيسية'
  },
  'nav.projects': {
    en: 'Projects',
    ar: 'المشاريع'
  },
  'nav.settings': {
    en: 'Settings',
    ar: 'الإعدادات'
  },
  'nav.logout': {
    en: 'Log Out',
    ar: 'تسجيل الخروج'
  },

  // Dashboard
  'dashboard.title': {
    en: 'AutoTest & DocGen Dashboard',
    ar: 'لوحة تحكم AutoTest & DocGen'
  },
  'dashboard.welcome': {
    en: 'Welcome to AutoTest & DocGen Dashboard!',
    ar: 'مرحباً بك في لوحة تحكم AutoTest & DocGen!'
  },
  'projects.title': {
    en: 'Projects workspace',
    ar: 'مساحة العمل للمشاريع'
  },
  'projects.description': {
    en: 'Organize your university projects and attach code artifacts.',
    ar: 'نظم مشاريعك الجامعية وأرفق ملفات الكود.'
  },
  'projects.refresh': {
    en: 'Refresh',
    ar: 'تحديث'
  },
  'projects.new': {
    en: 'New project',
    ar: 'مشروع جديد'
  },
  'projects.loading': {
    en: 'Loading projects...',
    ar: 'جاري تحميل المشاريع...'
  },
  'projects.error': {
    en: 'Error loading projects',
    ar: 'خطأ في تحميل المشاريع'
  },
  'projects.no_projects': {
    en: 'No Projects Yet',
    ar: 'لا توجد مشاريع بعد'
  },
  'projects.no_projects_message': {
    en: 'Get started by creating your first project!',
    ar: 'ابدأ بإنشاء أول مشروع لك!'
  },
  'projects.your_projects': {
    en: 'Your Projects',
    ar: 'مشاريعك'
  },
  'projects.owner': {
    en: 'Owner',
    ar: 'المالك'
  },
  'projects.actions': {
    en: 'Actions',
    ar: 'الإجراءات'
  },
  'projects.no_description': {
    en: 'No description',
    ar: 'لا يوجد وصف'
  },
  'projects.add_code': {
    en: 'Add code to this project',
    ar: 'إضافة كود لهذا المشروع'
  },
  'projects.edit': {
    en: 'Edit Project',
    ar: 'تعديل المشروع'
  },
  'projects.delete': {
    en: 'Delete Project',
    ar: 'حذف المشروع'
  },

  // Project Modal
  'project.create.title': {
    en: 'Create New Project',
    ar: 'إنشاء مشروع جديد'
  },
  'project.create.subtitle': {
    en: 'Give your project a clear name and an optional short description.',
    ar: 'أعطِ مشروعك اسماً واضحاً ووصفاً قصيراً اختيارياً.'
  },
  'project.edit.title': {
    en: 'Edit Project',
    ar: 'تعديل المشروع'
  },
  'project.edit.subtitle': {
    en: 'Update project title or description without affecting its artifacts.',
    ar: 'حدث اسم المشروع أو الوصف دون التأثير على ملفاته.'
  },
  'project.title.label': {
    en: 'Title',
    ar: 'العنوان'
  },
  'project.description.label': {
    en: 'Description',
    ar: 'الوصف'
  },
  'project.title.required': {
    en: 'Title is required.',
    ar: 'العنوان مطلوب.'
  },
  'project.title.length': {
    en: 'Title must be 255 characters or less.',
    ar: 'يجب أن يكون العنوان 255 حرفاً أو أقل.'
  },
  'project.create.button': {
    en: 'Create Project',
    ar: 'إنشاء المشروع'
  },
  'project.update.button': {
    en: 'Update Project',
    ar: 'تحديث المشروع'
  },
  'project.cancel': {
    en: 'Cancel',
    ar: 'إلغاء'
  },
  'project.creating': {
    en: 'Creating...',
    ar: 'جاري الإنشاء...'
  },
  'project.updating': {
    en: 'Updating...',
    ar: 'جاري التحديث...'
  },

  // Code Upload
  'code.upload.title': {
    en: 'Add code to',
    ar: 'إضافة كود إلى'
  },
  'code.upload.subtitle': {
    en: 'Attach a Python or Java file to this project to generate a class diagram.',
    ar: 'أرفق ملف Python أو Java لهذا المشروع لتوليد مخطط الكلاسات.'
  },
  'code.name.label': {
    en: 'Code Name',
    ar: 'اسم الكود'
  },
  'code.name.hint': {
    en: 'A short, meaningful name for this code unit.',
    ar: 'اسم قصير ومعنوي لهذه الوحدة من الكود.'
  },
  'code.file.label': {
    en: 'File Name',
    ar: 'اسم الملف'
  },
  'code.file.hint': {
    en: 'Optional – we will use the uploaded file name if left empty.',
    ar: 'اختياري - سنستخدم اسم الملف المرفوع إذا ترك فارغاً.'
  },
  'code.language.label': {
    en: 'Language',
    ar: 'اللغة'
  },
  'code.version.label': {
    en: 'Version',
    ar: 'الإصدار'
  },
  'code.text.label': {
    en: 'Code (optional if file is uploaded)',
    ar: 'الكود (اختياري إذا تم رفع ملف)'
  },
  'code.text.hint': {
    en: 'You can either paste code here or upload a .py / .java file below.',
    ar: 'يمكنك لصق الكود هنا أو رفع ملف .py / .java أدناه.'
  },
  'code.upload.label': {
    en: 'Or upload file',
    ar: 'أو رفع ملف'
  },
  'code.generate.button': {
    en: 'Generate Class Diagram',
    ar: 'توليد مخطط الكلاسات'
  },
  'code.processing': {
    en: 'Processing...',
    ar: 'جاري المعالجة...'
  },

  // Validation
  'validation.code.name.required': {
    en: 'Code name is required.',
    ar: 'اسم الكود مطلوب.'
  },
  'validation.code.required': {
    en: 'Please provide code text or upload a file.',
    ar: 'يرجى تقديم نص الكود أو رفع ملف.'
  },

  // Diagram
  'diagram.title': {
    en: 'Class Diagram',
    ar: 'مخطط الكلاسات'
  },
  'diagram.export': {
    en: 'Export PNG',
    ar: 'تصدير PNG'
  },
  'diagram.generating': {
    en: 'Generating class diagram, please wait...',
    ar: 'جاري توليد مخطط الكلاسات، يرجى الانتظار...'
  },
  'diagram.analyzing': {
    en: 'Analyzing your code, please wait...',
    ar: 'جاري تحليل الكود، يرجى الانتظار...'
  },

  // Common
  'common.back': {
    en: 'Back to Dashboard',
    ar: 'العودة للوحة التحكم'
  },
  'common.delete': {
    en: 'Delete',
    ar: 'حذف'
  },
  'common.edit': {
    en: 'Edit',
    ar: 'تعديل'
  },
  'common.add': {
    en: 'Add Code',
    ar: 'إضافة كود'
  },
  'common.success': {
    en: 'Success!',
    ar: 'نجح!'
  },
  'common.error': {
    en: 'Error',
    ar: 'خطأ'
  },

  // Language
  'lang.english': {
    en: 'English',
    ar: 'الإنجليزية'
  },
  'lang.arabic': {
    en: 'العربية',
    ar: 'العربية'
  }
};

class I18n {
  private currentLanguage: Language = 'en';

  setLanguage(language: Language) {
    this.currentLanguage = language;
    localStorage.setItem('language', language);
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
  }

  getLanguage(): Language {
    return this.currentLanguage;
  }

  t(key: string, params?: TranslationParams): string {
    const translation = translations[key];
    if (!translation) {
      console.warn(`Translation key "${key}" not found`);
      return key;
    }

    let text = translation[this.currentLanguage] || translation.en;

    // Handle interpolation with params
    if (params) {
      Object.keys(params).forEach(key => {
        text = text.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), params[key]);
        text = text.replace(new RegExp(`{${key}}`, 'g'), params[key]);
      });
    }

    return text;
  }

  // Initialize from localStorage
  init() {
    const savedLanguage = localStorage.getItem('language') as Language;
    if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'ar')) {
      this.setLanguage(savedLanguage);
    } else {
      // Auto-detect language from browser
      const browserLang = navigator.language || navigator.languages?.[0];
      if (browserLang?.startsWith('ar')) {
        this.setLanguage('ar');
      } else {
        this.setLanguage('en');
      }
    }
  }
}

export const i18n = new I18n();
