/**
 * إعدادات الـ API Gateway
 * تم ضبط المسارات لتتطابق مع ملف nginx.conf والـ Backend URLs
 * تم إصلاح مشكلة التكرار في البادئات والـ URLs المطلقة
 */

const API_BASE = import.meta.env.VITE_API_URL || '/';

// Direct base URLs for each microservice (used when going through proxy won't work for multipart)
export const DIRECT_SERVICE_URLS = {
  UPM: import.meta.env.VITE_UPM_URL || 'http://localhost:8001',
  AI: import.meta.env.VITE_AI_URL || 'http://localhost:8002',
} as const;

export const API_CONFIG = {
  BASE_URL: API_BASE,
  // البادئات التعريفية لكل خدمة - تم الإصلاح لإزالة التكرار
  PREFIX: {
    UPM: '/api/upm',           // ✅ إصلاح: المسار الكامل للـ proxy
    AI: '/api/analysis',       // ✅ إصلاح: المسار الكامل للـ proxy  
    NOTIFICATIONS: '/api/notifications', // ✅ إصلاح: المسار الكامل للـ proxy
    AUTH_TOKEN: '/api/token',  // ✅ إصلاح: المسار الكامل للـ proxy
  },
  TIMEOUT: 60000, // زيادة timeout لـ 60 ثانية للعمليات الطويلة كرفع المجلدات
} as const;

/**
 * دالة مساعدة لبناء الرابط الكامل بناءً على الخدمة المستهدفة
 * تم الإصلاح لإزالة التكرار وضمان الـ relative URLs
 */
const buildUrl = (servicePrefix: string, endpoint: string): string => {
  // تنظيف endpoint من أي بادئة /api/ مكررة
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // إزالة أي تكرار لـ /api/ من البداية
  if (cleanEndpoint.startsWith('/api/')) {
    cleanEndpoint = cleanEndpoint.replace(/^\/api\//, '/');
  }

  // ضمان أن servicePrefix لا ينتهي بسلاش
  const cleanPrefix = servicePrefix.endsWith('/')
    ? servicePrefix.slice(0, -1)
    : servicePrefix;

  // بناء الرابط النسبي الكامل
  const fullUrl = `${cleanPrefix}${cleanEndpoint}`;

  // Log for debugging
  console.log('Building URL:', { API_BASE, servicePrefix, endpoint, cleanPrefix, cleanEndpoint, fullUrl });

  return fullUrl;
};

export const API_ENDPOINTS = {
  // 1. المصادقة (موجهة لخدمة UPM)
  auth: {
    signup: () => buildUrl(API_CONFIG.PREFIX.UPM, 'signup/'),           // → /api/upm/signup/
    login: () => buildUrl(API_CONFIG.PREFIX.UPM, 'login/'),             // → /api/upm/login/
    refreshToken: () => buildUrl(API_CONFIG.PREFIX.AUTH_TOKEN, 'refresh/'), // → /api/token/refresh/
    verifyToken: () => buildUrl(API_CONFIG.PREFIX.AUTH_TOKEN, 'verify/'),   // → /api/token/verify/
    deleteAccount: () => buildUrl(API_CONFIG.PREFIX.UPM, 'delete-account/'), // → /api/upm/delete-account/
  },

  // 2. خدمة المشاريع (UPM Service)
  projects: {
    list: () => buildUrl(API_CONFIG.PREFIX.UPM, 'projects/'),           // → /api/upm/projects/
    create: () => buildUrl(API_CONFIG.PREFIX.UPM, 'projects/'),         // → /api/upm/projects/
    detail: (id: string) => buildUrl(API_CONFIG.PREFIX.UPM, `projects/${id}/`), // → /api/upm/projects/{id}/
    artifacts: (projectId: string) => buildUrl(API_CONFIG.PREFIX.UPM, `projects/${projectId}/artifacts/`), // → /api/upm/projects/{id}/artifacts/
    // ✅ رفع مجلد/ZIP كامل للمشروع
    folderUpload: (projectId: string) => buildUrl(API_CONFIG.PREFIX.UPM, `projects/${projectId}/folder-upload/`), // → /api/upm/projects/{id}/folder-upload/
  },

  // 3. خدمة تحليل الكود (AI Service) - تتبع /api/ في Nginx
  analysis: {
    // ==================== Code Files Endpoints ====================
    // إنشاء أو رفع ملف كود جديد (POST) - يدعم multipart/form-data
    codefiles: () => buildUrl(API_CONFIG.PREFIX.AI, 'codefiles/'),      // → /api/analysis/codefiles/
    start: () => buildUrl(API_CONFIG.PREFIX.AI, 'start/'),              // → /api/analysis/start/

    codefileDetail: (id: string) => buildUrl(API_CONFIG.PREFIX.AI, `codefiles/${id}/`), // → /api/analysis/codefiles/{id}/
    codefileAnalyze: (id: string) => buildUrl(API_CONFIG.PREFIX.AI, `codefiles/${id}/analyze/`), // → /api/analysis/codefiles/{id}/analyze/
    codefilesByProject: (projectId: string) => buildUrl(API_CONFIG.PREFIX.AI, `codefiles/?project_id=${projectId}`), // → /api/analysis/codefiles/?project_id=xxx

    // ==================== Analysis Workflow ====================
    analyze: () => buildUrl(API_CONFIG.PREFIX.AI, 'analyze/'),          // → /api/analysis/analyze/

    // ✅ تحليل مشروع كامل (Large Project Processing)
    analyzeProject: () => buildUrl(API_CONFIG.PREFIX.AI, 'analyze-project/'), // → /api/analysis/analyze-project/  (POST: {project_id})
    analyzeProjectStatus: (projectId: string) => buildUrl(API_CONFIG.PREFIX.AI, `analyze-project/?project_id=${projectId}`), // → /api/analysis/analyze-project/?project_id=xxx (GET)
    projectClassDiagram: (projectId: string) => buildUrl(API_CONFIG.PREFIX.AI, `project-class-diagram/${projectId}/`), // → /api/analysis/project-class-diagram/{id}/

    // ==================== Analysis Jobs Endpoints ====================
    jobs: () => buildUrl(API_CONFIG.PREFIX.AI, 'jobs/'),              // → /api/analysis/jobs/
    jobDetail: (id: string) => buildUrl(API_CONFIG.PREFIX.AI, `jobs/${id}/`), // → /api/analysis/jobs/{id}/

    // ==================== Analysis Results Endpoints ====================
    results: (jobId?: string) => jobId ? buildUrl(API_CONFIG.PREFIX.AI, `analysis-results/${jobId}/`) : buildUrl(API_CONFIG.PREFIX.AI, 'analysis-results/'), // → /api/analysis/analysis-results/
    result: (id: string) => buildUrl(API_CONFIG.PREFIX.AI, `analysis-results/${id}/`), // → /api/analysis/analysis-results/{id}/
    taskStatus: (taskId: string) => buildUrl(API_CONFIG.PREFIX.AI, `task-status/${taskId}/`), // → /api/analysis/task-status/{id}/
    classDiagram: (id: string) => buildUrl(API_CONFIG.PREFIX.AI, `analysis-results/${id}/class_diagram/`), // → /api/analysis/analysis-results/{id}/class_diagram/

    // ==================== Export & Documentation ====================
    // تصدير توثيق (GET)
    // Query params: format=pdf|md, type=high|low|detailed, mode=display|download
    export: (analysisId: string) => buildUrl(API_CONFIG.PREFIX.AI, `export/${analysisId}/`), // → /api/analysis/export/{id}/
    generatedFiles: () => buildUrl(API_CONFIG.PREFIX.AI, 'generated-files/'), // → /api/analysis/generated-files/
    downloadGeneratedFile: (fileId: string) => buildUrl(API_CONFIG.PREFIX.AI, `download-generated-file/${fileId}/`), // → /api/analysis/download-generated-file/{id}/

    // ==================== Artifacts Management ====================
    saveArtifact: () => buildUrl(API_CONFIG.PREFIX.AI, 'artifacts/'),    // → /api/analysis/artifacts/
    getProjectArtifacts: (projectId: string) => buildUrl(API_CONFIG.PREFIX.AI, `artifacts/?project_id=${projectId}`), // → /api/analysis/artifacts/?project_id=xxx
    updateArtifact: (artifactId: string) => buildUrl(API_CONFIG.PREFIX.AI, `artifacts/${artifactId}/`), // → /api/analysis/artifacts/{id}/
    generateDocument: () => buildUrl(API_CONFIG.PREFIX.AI, 'generate-document/'), // → /api/analysis/generate-document/

    // ==================== AI Explanations Endpoints ====================
    aiExplanations: () => buildUrl(API_CONFIG.PREFIX.AI, 'ai-explanations/'), // → /api/analysis/ai-explanations/
    generateExplanation: () => buildUrl(API_CONFIG.PREFIX.AI, 'ai-explanations/generate-explanation/'), // → /api/analysis/ai-explanations/generate-explanation/
    explanationTaskStatus: (taskId: string) => buildUrl(API_CONFIG.PREFIX.AI, `ai-explanations/task-status/?task_id=${taskId}`), // → /api/analysis/ai-explanations/task-status/?task_id=xxx
    explanationAnalysisTasks: (analysisId: string) => buildUrl(API_CONFIG.PREFIX.AI, `ai-explanations/analysis-tasks/?analysis_id=${analysisId}`), // → /api/analysis/ai-explanations/analysis-tasks/?analysis_id=xxx
    exportLegacy: () => buildUrl(API_CONFIG.PREFIX.AI, 'ai-explanations/export-legacy/'), // → /api/analysis/ai-explanations/export-legacy/
  },

  // 4. خدمة الإشعارات (Notification Service)
  notifications: {
    // Notification types endpoints
    project: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'project/'), // → /api/notifications/project/
    code: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'code/'),       // → /api/notifications/code/
    documentation: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'documentation/'), // → /api/notifications/documentation/
    user: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'user/'),       // → /api/notifications/user/
    system: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'system/'),   // → /api/notifications/system/
    custom: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'custom/'),   // → /api/notifications/custom/
    settings: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'settings/'), // → /api/notifications/settings/

    // Notification management endpoints
    list: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, ''),            // → /api/notifications/
    stats: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'stats/'),     // → /api/notifications/stats/
    markAllRead: () => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, 'mark-all-read/'), // → /api/notifications/mark-all-read/
    detail: (id: string) => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, `${id}/`), // → /api/notifications/{id}/
    markRead: (id: string) => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, `${id}/mark-read/`), // → /api/notifications/{id}/mark-read/
    delete: (id: string) => buildUrl(API_CONFIG.PREFIX.NOTIFICATIONS, `${id}/delete/`), // → /api/notifications/{id}/delete/
  },

  // 6. خدمة شرح المنطق (Logic Explanation Service)
  logicExplanation: {
    levels: () => buildUrl(API_CONFIG.PREFIX.AI, 'ai-explanations/'),     // → /api/analysis/ai-explanations/
    explain: () => buildUrl(API_CONFIG.PREFIX.AI, 'ai-explanations/generate-explanation/'), // → /api/analysis/ai-explanations/generate-explanation/
    projectFiles: (projectId: string) => buildUrl(API_CONFIG.PREFIX.AI, `ai-explanations/analysis-tasks/?project_id=${projectId}`), // → /api/analysis/ai-explanations/analysis-tasks/?project_id=xxx
  },

  // 5. روابط التوثيق (Swagger & ReDoc)
  docs: {
    upmSwagger: '/swagger-upm/',
    aiSwagger: '/swagger-ai/',
  },

  // 6. Health Check
  health: () => '/health/',
} as const;

// ==================== Helper Functions ====================

/**
 * دالة مساعدة لإنشاء FormData لرفع ملف كود
 */
export const createCodeFileFormData = (
  file: File,
  projectId: string,
  language: 'python' | 'java'
): FormData => {
  const formData = new FormData();
  formData.append('uploaded_file', file);
  formData.append('filename', file.name);
  formData.append('file_type', language);
  formData.append('source_project_id', projectId);
  return formData;
};

/**
 * دالة مساعدة لإنشاء body لرفع محتوى كود نصي
 */
export const createCodeFileBody = (
  content: string,
  filename: string,
  projectId: string,
  language: 'python' | 'java'
) => {
  return {
    content: content,
    filename: filename,
    file_type: language,
    source_project_id: projectId
  };
};

/**
 * دالة مساعدة لبدء عملية تحليل
 */
export const createAnalysisBody = (
  codeFileId: string,
  analysisType: 'class_diagram' | 'explanation' = 'class_diagram',
  explanationLevel?: 'high' | 'low'
) => {
  const body: any = {
    code_file_id: codeFileId,
    analysis_type: analysisType
  };

  if (analysisType === 'explanation' && explanationLevel) {
    body.explanation_level = explanationLevel;
  }

  return body;
};
