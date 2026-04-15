import { type AxiosInstance } from 'axios';
import apiClient from './apiClient'; // ✅ استخدام apiClient الموجود
import { API_ENDPOINTS } from '../config/api.config';

// ----------------------------------------------------
// تعريف الـ TYPES الأساسية
// ----------------------------------------------------

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export interface ProjectCode {
    id: string;
    code_name: string;
    file_name: string;
    language: 'python' | 'java';
    version: string;
    created_at: string;
    updated_at: string;
}

export interface ProjectDocumentation {
    id: string;
    name: string;
    type: 'class_diagram' | 'logic_explanation' | 'api_docs';
    created_at: string;
    file_path?: string;
}

export interface Project {
    id: string;
    title: string;
    description: string;
    user: number;
    username: string;
    created_at: string;
    updated_at: string;
    codes?: ProjectCode[];
    documentation?: ProjectDocumentation[];
}

export interface CreateProjectData {
    title: string;
    description: string;
}

export interface UpdateProjectData {
    title?: string;
    description?: string;
}

// Auth Types
export interface LoginData {
    username: string;
    password: string;
}

export interface SignupData {
    username: string;
    email: string;
    password: string;
}

export interface UserRole {
    id: number;
    role_name: string;
    description: string;
    permissions_list: Record<string, unknown>;
}

export interface UserProfile {
    full_name: string;
    signup_date: string;
    role: UserRole | null;
}

export interface User {
    id: number;
    username: string;
    email: string;
    profile: UserProfile | null;
}

export interface AuthResponse {
    access: string;
    refresh: string;
    user: User;
}

export interface SignupResponse {
    id: number;
    username: string;
    email: string;
    profile: UserProfile | null;
}

export interface CurrentUser {
    id: number;
    username: string;
    email: string;
    profile: UserProfile | null;
}

// ----------------------------------------------------
// Error handling helper
// ----------------------------------------------------
export interface ApiError {
    detail?: string;
    [key: string]: string[] | string | undefined;
}

export const formatApiError = (error: any): string => {
    if (error.response?.data) {
        const errorData: ApiError = error.response.data;

        if (errorData.detail) {
            return errorData.detail;
        }

        const fieldErrors: string[] = [];
        for (const [key, value] of Object.entries(errorData)) {
            if (Array.isArray(value) && value.length > 0) {
                fieldErrors.push(`${key}: ${value.join(', ')}`);
            } else if (typeof value === 'string') {
                fieldErrors.push(`${key}: ${value}`);
            }
        }

        if (fieldErrors.length > 0) {
            return fieldErrors.join('; ');
        }
    }

    return error.message || 'An unexpected error occurred';
};

// ----------------------------------------------------
// BaseService (الخدمة الأساسية لـ CRUD)
// ----------------------------------------------------
class BaseService {
    protected apiClient: AxiosInstance = apiClient;

    protected async get<T>(url: string): Promise<T> {
        const response = await this.apiClient.get<T>(url);
        if (!response.data) {
            throw new Error(`API returned success for ${url} but the data body was empty.`);
        }
        return response.data;
    }

    protected async post<T, D>(url: string, data: D): Promise<T> {
        const response = await this.apiClient.post<T>(url, data);
        return response.data;
    }

    protected async patch<T, D>(url: string, data: D): Promise<T> {
        const response = await this.apiClient.patch<T>(url, data);
        return response.data;
    }

    protected async delete(url: string): Promise<void> {
        await this.apiClient.delete(url);
    }
}

// ----------------------------------------------------
// AuthService Class
// ----------------------------------------------------
class AuthService extends BaseService {
    async login(credentials: LoginData): Promise<AuthResponse> {
        return this.post<AuthResponse, LoginData>(API_ENDPOINTS.auth.login(), credentials);
    }

    async signup(data: SignupData): Promise<SignupResponse> {
        return this.post<SignupResponse, SignupData>(API_ENDPOINTS.auth.signup(), data);
    }

    async refreshToken(refresh: string): Promise<{ access: string }> {
        const response = await this.apiClient.post<{ access: string }>(
            API_ENDPOINTS.auth.refreshToken(),
            { refresh }
        );
        return response.data;
    }

    async verifyToken(token: string): Promise<boolean> {
        try {
            await this.apiClient.post(API_ENDPOINTS.auth.verifyToken(), { token });
            return true;
        } catch {
            return false;
        }
    }

    async deleteAccount(): Promise<void> {
        return this.delete(API_ENDPOINTS.auth.deleteAccount());
    }
}

// Class diagram data interface
export interface ClassDiagramData {
    mermaid: string;
}

// Logic explanation types
export interface LogicExplanationLevel {
    id: string;
    name: string;
    description: string;
    icon: string;
    suitable_for: string;
}

export interface LogicExplanationRequest {
    code_content: string;
    level: 'high_level' | 'low_level';
    code_name: string;
    file_name: string;
    project_id?: string;
}

export interface LogicExplanationResponse {
    code_name: string;
    file_name: string;
    explanation_level: string;
    level_display: string;
    explanation: string;
    code_preview: string;
    timestamp: string;
    metadata: {
        code_length: number;
        level: string;
        model_used: string;
    };
}

export interface ProjectCodeFile {
    id: string;
    project_id: string;
    file_name: string;
    language: string;
    size: number;
    last_modified: string;
    code_preview: string;
    status: string;
}

// Code file interfaces
export interface CreateCodeFileData {
    filename: string;
    file_type: string;
    content: string;
    source_project_id?: string;
}

export interface CodeFile {
    id: string;
    filename: string;
    file_type: string;
    content: string;
    uploaded_at: string;
    source_project_id?: string;
    analysis_status: string;
}

// Analysis interfaces
export interface StartAnalysisData {
    code_file_id: string;
    analysis_type: 'class_diagram' | 'explanation';
    explanation_level?: 'high' | 'low';
}

export interface GenerateExplanationData {
    analysis_id: string;
    type: 'high' | 'low';
}

export interface TaskStatusResponse {
    task_id: string;
    status: string;
    analysis_id?: string;
    exp_type?: string;
    created_at?: string;
    message?: string;
    progress?: number;
    result?: any;
    completed_at?: string;
    error?: string;
}

export interface GeneratedFile {
    _id: string;
    filename: string;
    file_type: string;
    explanation_id?: string;
    analysis_id?: string;
    created_at: string;
    file_size?: number;
    downloaded_count?: number;
}

// ----------------------------------------------------
// ApiService Class - يستخدم apiClient المُهيّأ
// ----------------------------------------------------
export class ApiService extends BaseService {
    // ==================== Health Check ====================
    async healthCheck(): Promise<{ status: string }> {
        return this.get<{ status: string }>(API_ENDPOINTS.health());
    }

    // ==================== Projects ====================

    async getProjects(page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<Project>> {
        const url = `${API_ENDPOINTS.projects.list()}?page=${page}&page_size=${pageSize}`;
        return this.get<PaginatedResponse<Project>>(url);
    }

    async getProject(id: string): Promise<Project> {
        return this.get<Project>(API_ENDPOINTS.projects.detail(id));
    }

    async createProject(projectData: CreateProjectData): Promise<Project> {
        return this.post<Project, CreateProjectData>(API_ENDPOINTS.projects.create(), projectData);
    }

    async updateProject(id: string, projectData: UpdateProjectData): Promise<Project> {
        return this.patch<Project, UpdateProjectData>(API_ENDPOINTS.projects.detail(id), projectData);
    }

    async deleteProject(id: string): Promise<void> {
        return this.delete(API_ENDPOINTS.projects.detail(id));
    }

    // ==================== Code Files ====================

    async createCodeFile(codeFileData: CreateCodeFileData): Promise<CodeFile> {
        // For FormData uploads, use the AI codefiles endpoint directly
        if (codeFileData instanceof FormData) {
            return this.post<CodeFile, FormData>(`/api/analysis/codefiles/`, codeFileData);
        }
        // For JSON uploads, use original endpoint
        return this.post<CodeFile, CreateCodeFileData>(API_ENDPOINTS.analysis.codefiles(), codeFileData);
    }

    async getCodeFile(codeFileId: string): Promise<CodeFile> {
        return this.get<CodeFile>(API_ENDPOINTS.analysis.codefileDetail(codeFileId));
    }

    async analyzeCodeFile(codeFileId: string): Promise<any> {
        return this.post<any, {}>(API_ENDPOINTS.analysis.codefileAnalyze(codeFileId), {});
    }

    async getCodeFilesByProject(projectId: string): Promise<CodeFile[]> {
        const response = await this.get<{ code_files: CodeFile[] }>(
            API_ENDPOINTS.analysis.codefilesByProject(projectId)
        );
        return response.code_files || [];
    }

    // ==================== Analysis ====================

    async startAnalysis(data: StartAnalysisData): Promise<any> {
        return this.post<any, StartAnalysisData>(API_ENDPOINTS.analysis.analyze(), data);
    }

    async getAnalysisResults(jobId?: string): Promise<any[]> {
        let url = API_ENDPOINTS.analysis.results();
        if (jobId) {
            url = API_ENDPOINTS.analysis.results(jobId);
        }

        console.log('🔍 [DEBUG] Fetching analysis results from URL:', url);
        console.log('🔍 [DEBUG] Job ID parameter:', jobId);

        const response = await this.get<PaginatedResponse<any> | any[]>(url);

        console.log('🔍 [DEBUG] Analysis results response:', response);

        if (Array.isArray(response)) {
            console.log('🔍 [DEBUG] Response is array, length:', response.length);
            return response;
        } else if (response && 'results' in response) {
            console.log('🔍 [DEBUG] Response has results property, count:', response.results?.length);
            return response.results;
        }
        console.log('🔍 [DEBUG] No valid results found, returning empty array');
        return [];
    }

    async getAnalysisResult(resultId: string): Promise<any> {
        const url = API_ENDPOINTS.analysis.result(resultId);
        console.log('🔍 [DEBUG] Fetching analysis result from URL:', url);
        console.log('🔍 [DEBUG] Result ID:', resultId);

        const response = await this.get<any>(url);
        console.log('🔍 [DEBUG] Analysis result response:', response);
        return response;
    }

    async getClassDiagram(analysisResultId: string): Promise<ClassDiagramData> {
        const url = API_ENDPOINTS.analysis.classDiagram(analysisResultId);
        console.log('🔍 [DEBUG] Fetching class diagram from URL:', url);
        console.log('🔍 [DEBUG] Analysis Result ID:', analysisResultId);

        const response = await this.get<any>(url);
        console.log('🔍 [DEBUG] Class diagram response:', response);

        let mermaidCode = '';
        if (response.mermaid_code) {
            mermaidCode = response.mermaid_code;
            console.log('🔍 [DEBUG] Found mermaid_code in response');
        } else if (response.class_diagram_data) {
            if (typeof response.class_diagram_data === 'string') {
                mermaidCode = response.class_diagram_data;
                console.log('🔍 [DEBUG] Found class_diagram_data as string');
            } else if (response.class_diagram_data.mermaid_code) {
                mermaidCode = response.class_diagram_data.mermaid_code;
                console.log('🔍 [DEBUG] Found mermaid_code in class_diagram_data object');
            }
        }

        console.log('🔍 [DEBUG] Final mermaid code length:', mermaidCode.length);
        return { mermaid: mermaidCode };
    }

    // ==================== AI Explanations ====================

    async getAIExplanations(): Promise<any[]> {
        return this.get<any[]>(API_ENDPOINTS.analysis.aiExplanations());
    }

    async generateAIExplanation(data: GenerateExplanationData): Promise<any> {
        // Normalize frontend param to backend expected `exp_type` (accepts 'high' | 'low')
        const payload = {
            analysis_id: data.analysis_id,
            exp_type: data.type // backend expects `exp_type` like 'high' or 'low'
        } as any;

        return this.post<any, any>(
            API_ENDPOINTS.analysis.generateExplanation(),
            payload
        );
    }

    async getExplanationTaskStatus(taskId: string): Promise<TaskStatusResponse> {
        return this.get<TaskStatusResponse>(API_ENDPOINTS.analysis.explanationTaskStatus(taskId));
    }

    async getAnalysisTasks(analysisId: string): Promise<any> {
        return this.get<any>(API_ENDPOINTS.analysis.explanationAnalysisTasks(analysisId));
    }

    // ==================== Export & Files ====================

    async exportDocumentation(
        analysisId: string,
        format: 'pdf' | 'md' | 'markdown' | 'html' | 'xml',
        type: 'high' | 'low' | 'detailed',
        mode?: 'display' | 'download',
        imageUrl?: string,
        userEmail?: string
    ): Promise<Blob> {
        const params = new URLSearchParams({
            format,
            type,
            ...(mode && { mode }),
            ...(imageUrl && { image_url: imageUrl }),
            ...(userEmail && { user_email: userEmail })
        });

        const url = `${API_ENDPOINTS.analysis.export(analysisId)}?${params.toString()}`;

        const response = await this.apiClient.get(url, { responseType: 'blob' });
        return response.data;
    }

    buildLegacyExportUrl(
        analysisId: string,
        format: 'pdf' | 'md' | 'html' | 'xml',
        level: 'high' | 'low'
    ): string {
        return `/api/explanation/export-legacy/?id=${analysisId}&format=${format}&level=${level}`;
    }

    async getGeneratedFiles(projectId?: string): Promise<any[]> {
        try {
            const url = projectId
                ? `/api/analysis/generated-files/?project_id=${projectId}`
                : `/api/analysis/generated-files/`;
            const response = await this.get<any>(url);
            return response?.files || response || [];
        } catch (error) {
            console.error('Failed to fetch generated files:', error);
            return [];
        }
    }

    async downloadGeneratedFile(fileId: string): Promise<Blob> {
        const response = await this.apiClient.get(
            API_ENDPOINTS.analysis.downloadGeneratedFile(fileId),
            { responseType: 'blob' }
        );
        return response.data;
    }

    async generateDocument(data: any): Promise<any> {
        return this.post<any, any>(API_ENDPOINTS.analysis.generateDocument(), data);
    }

    // ==================== Legacy Methods ====================

    async getLogicExplanationLevels(): Promise<LogicExplanationLevel[]> {
        return this.get<LogicExplanationLevel[]>(API_ENDPOINTS.logicExplanation.levels());
    }

    async explainCodeLogic(requestData: LogicExplanationRequest): Promise<LogicExplanationResponse> {
        return this.post<LogicExplanationResponse, LogicExplanationRequest>(
            API_ENDPOINTS.logicExplanation.explain(),
            requestData
        );
    }

    async getProjectCodeFiles(projectId: string): Promise<ProjectCodeFile[]> {
        const url = API_ENDPOINTS.logicExplanation.projectFiles(projectId);
        return this.get<ProjectCodeFile[]>(url);
    }

    async getProjectCodes(projectId: string): Promise<ProjectCode[]> {
        try {
            // Try the AI codefiles endpoint — artifacts endpoint doesn't exist
            const response = await this.get<any>(`/api/analysis/codefiles/?project_id=${projectId}`);
            const items: any[] = Array.isArray(response) ? response : (response?.results || response?.code_files || []);

            return items.map(item => ({
                id: item.id || item._id,
                code_name: item.filename || item.code_name || item.file_name || 'Unknown',
                file_name: item.filename || item.file_name || 'Unknown',
                language: item.file_type || item.language || 'python',
                version: item.version || '1.0',
                created_at: item.uploaded_at || item.created_at,
                updated_at: item.updated_at,
            }));
        } catch (error) {
            console.warn('Could not fetch project codes — non-critical, continuing:', error);
            return [];
        }
    }

    async getProjectDocumentation(projectId: string): Promise<ProjectDocumentation[]> {
        try {
            // Use generated-files endpoint — artifacts endpoint doesn't exist
            const response = await this.get<any>(`/api/analysis/generated-files/?project_id=${projectId}`);
            const items: any[] = Array.isArray(response) ? response : (response?.files || response?.results || []);

            return items.map(item => ({
                id: item._id || item.id,
                name: item.filename || item.file_name || 'Unknown',
                type: item.file_type || 'class_diagram',
                created_at: item.created_at,
                file_path: item.file_path,
            }));
        } catch (error) {
            console.warn('Could not fetch project documentation — non-critical:', error);
            return [];
        }
    }
}

// ----------------------------------------------------
// NotificationService Class
// ----------------------------------------------------
export interface Notification {
    id: string;
    title: string;
    message: string;
    type: string;
    notification_type: string;
    is_read: boolean;
    created_at: string;
    action_url?: string;
    action_text?: string;
    related_id?: string;
    related_type?: string;
}

class NotificationService extends BaseService {
    async getNotifications(params?: {
        user_email?: string;
        user_id?: string;
        is_read?: boolean;
        type?: string;
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<Notification>> {
        const queryParams = new URLSearchParams();

        if (params?.user_email) queryParams.append('user_email', params.user_email);
        if (params?.user_id) queryParams.append('user_id', params.user_id);
        if (params?.is_read !== undefined) queryParams.append('is_read', params.is_read.toString());
        if (params?.type) queryParams.append('type', params.type);
        if (params?.page) queryParams.append('page', params.page.toString());
        if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

        const url = `${API_ENDPOINTS.notifications.list()}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return this.get<PaginatedResponse<Notification>>(url);
    }

    async getNotification(notificationId: string): Promise<Notification> {
        return this.get<Notification>(API_ENDPOINTS.notifications.detail(notificationId));
    }

    async markNotificationAsRead(notificationId: string): Promise<Notification> {
        return this.patch<Notification, {}>(API_ENDPOINTS.notifications.markRead(notificationId), {});
    }

    async markAllNotificationsAsRead(params?: { user_email?: string; user_id?: string }): Promise<{ message: string; updated_count: number }> {
        return this.post<{ message: string; updated_count: number }, typeof params>(
            API_ENDPOINTS.notifications.markAllRead(),
            params || {}
        );
    }

    async deleteNotification(notificationId: string): Promise<void> {
        return this.delete(API_ENDPOINTS.notifications.delete(notificationId));
    }

    async getNotificationStats(params?: { user_email?: string; user_id?: string }): Promise<{ total: number; unread: number; read: number }> {
        const queryParams = new URLSearchParams();
        if (params?.user_email) queryParams.append('user_email', params.user_email);
        if (params?.user_id) queryParams.append('user_id', params.user_id);

        const url = `${API_ENDPOINTS.notifications.stats()}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return this.get<{ total: number; unread: number; read: number }>(url);
    }

    // ==================== Send Notifications ====================

    async sendNotification(data: {
        user_email: string;
        user_name?: string;
        user_id?: string;
        notification_type: string;
        title: string;
        message: string;
        action_url?: string;
        action_text?: string;
        related_type?: string;
        related_id?: string;
        priority?: string;
        extra_data?: any;
    }): Promise<any> {
        return this.post<any, typeof data>(API_ENDPOINTS.notifications.custom(), data);
    }

    async sendProjectNotification(data: {
        user_email: string;
        action: 'created' | 'deleted';
        project_name: string;
        project_id?: string;
        user_name?: string;
        user_id?: string;
    }): Promise<any> {
        return this.post<any, typeof data>(API_ENDPOINTS.notifications.project(), data);
    }

    async sendCodeNotification(data: {
        user_email: string;
        action: 'added' | 'deleted';
        code_name: string;
        project_name: string;
        code_id?: string;
        user_name?: string;
        user_id?: string;
    }): Promise<any> {
        return this.post<any, typeof data>(API_ENDPOINTS.notifications.code(), data);
    }

    async sendDocumentationNotification(data: {
        user_email: string;
        file_name: string;
        file_type: string;
        project_name?: string;
        user_name?: string;
        user_id?: string;
    }): Promise<any> {
        return this.post<any, typeof data>(API_ENDPOINTS.notifications.documentation(), data);
    }
}

// ----------------------------------------------------
// ✅ Default Export - مُحسّن مع جميع الخدمات
// ----------------------------------------------------
const authService = new AuthService();
const apiServiceInstance = new ApiService();
const notificationService = new NotificationService();

const apiService = {
    auth: authService,
    api: apiServiceInstance,
    notifications: notificationService,

    // ✅ Shortcuts للوصول السريع
    projects: {
        list: (page?: number, pageSize?: number) => apiServiceInstance.getProjects(page, pageSize),
        get: (id: string) => apiServiceInstance.getProject(id),
        create: (data: CreateProjectData) => apiServiceInstance.createProject(data),
        update: (id: string, data: UpdateProjectData) => apiServiceInstance.updateProject(id, data),
        delete: (id: string) => apiServiceInstance.deleteProject(id),
        getCodes: (projectId: string) => apiServiceInstance.getProjectCodes(projectId),
        getDocs: (projectId: string) => apiServiceInstance.getProjectDocumentation(projectId),
        getGeneratedFiles: (projectId?: string) => apiServiceInstance.getGeneratedFiles(projectId),
    },

    analysis: {
        // Code Files
        createCodeFile: (data: CreateCodeFileData) => apiServiceInstance.createCodeFile(data),
        getCodeFile: (id: string) => apiServiceInstance.getCodeFile(id),
        analyzeCodeFile: (id: string) => apiServiceInstance.analyzeCodeFile(id),
        getCodeFilesByProject: (projectId: string) => apiServiceInstance.getCodeFilesByProject(projectId),

        // Analysis
        startAnalysis: (data: StartAnalysisData) => apiServiceInstance.startAnalysis(data),
        getResults: (jobId?: string) => apiServiceInstance.getAnalysisResults(jobId),
        getResult: (id: string) => apiServiceInstance.getAnalysisResult(id),
        getClassDiagram: (id: string) => apiServiceInstance.getClassDiagram(id),

        // AI Explanations
        getExplanations: () => apiServiceInstance.getAIExplanations(),
        generateExplanation: (data: GenerateExplanationData) => apiServiceInstance.generateAIExplanation(data),
        getTaskStatus: (taskId: string) => apiServiceInstance.getExplanationTaskStatus(taskId),
        getTasks: (analysisId: string) => apiServiceInstance.getAnalysisTasks(analysisId),

        // Export & Files
        export: (
            analysisId: string,
            format: 'pdf' | 'md' | 'markdown' | 'html' | 'xml',
            type: 'high' | 'low' | 'detailed',
            mode?: 'display' | 'download',
            imageUrl?: string,
            userEmail?: string
        ) => apiServiceInstance.exportDocumentation(analysisId, format, type, mode, imageUrl, userEmail),
        buildLegacyExportUrl: (
            analysisId: string,
            format: 'pdf' | 'md' | 'html' | 'xml',
            level: 'high' | 'low'
        ) => apiServiceInstance.buildLegacyExportUrl(analysisId, format, level),
        getGeneratedFiles: () => apiServiceInstance.getGeneratedFiles(),
        downloadFile: (fileId: string) => apiServiceInstance.downloadGeneratedFile(fileId),
    },

    // ✅ Notification shortcuts
    sendNotification: (data: Parameters<typeof notificationService.sendNotification>[0]) =>
        notificationService.sendNotification(data),
    sendProjectNotification: (data: Parameters<typeof notificationService.sendProjectNotification>[0]) =>
        notificationService.sendProjectNotification(data),
    sendCodeNotification: (data: Parameters<typeof notificationService.sendCodeNotification>[0]) =>
        notificationService.sendCodeNotification(data),
    sendDocumentationNotification: (data: Parameters<typeof notificationService.sendDocumentationNotification>[0]) =>
        notificationService.sendDocumentationNotification(data),
};

export default apiService;
