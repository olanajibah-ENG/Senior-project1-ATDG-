// files.service.ts
// Unified service for handling code files, uploads, and analysis
// مدمج مع api.service.ts ويستخدم نفس المسارات الموحدة

import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api.config';

export interface CodeFile {
    id: string;
    filename: string;
    file_type: 'python' | 'java';
    created_at: string;
    updated_at: string;
    source_project_id?: string;
    content?: string; // Optional, loaded on demand
}

export interface CodeFileUploadResponse {
    id: string;
    filename: string;
    file_type: 'python' | 'java';
    source_project_id: string;
    created_at: string;
    updated_at: string;
}

export interface AnalysisStartResponse {
    task_id: string;
    code_file_id: string;
    analysis_type: 'class_diagram' | 'explanation';
    status: 'pending' | 'running' | 'completed' | 'failed';
    created_at: string;
}

export class FilesService {
    /**
     * رفع ملف كود جديد إلى الخادم
     * POST /api/upm/projects/{projectId}/artifacts/
     * يدعم multipart/form-data
     */
    static async uploadCodeFile(
        file: File,
        projectId: string,
        language: 'python' | 'java'
    ): Promise<CodeFileUploadResponse> {
        try {
            const formData = new FormData();
            formData.append('uploaded_file', file);
            formData.append('file_name', file.name);
            formData.append('code_language', language);

            // ✅ Use relative URL to work with apiClient baseURL
            const response = await apiClient.post<CodeFileUploadResponse>(
                `api/upm/projects/${projectId}/artifacts/`,
                formData
            );
            return response.data;
        } catch (error) {
            console.error('Failed to upload code file:', error);
            throw error;
        }
    }

    /**
     * رفع ملفات كود متعددة
     * POST /api/upm/projects/{projectId}/artifacts/
     */
    static async uploadCodeFiles(
        files: File[],
        projectId: string,
        language: 'python' | 'java'
    ): Promise<CodeFileUploadResponse[]> {
        try {
            const responses = await Promise.all(
                files.map(file =>
                    this.uploadCodeFile(file, projectId, language)
                )
            );
            return responses;
        } catch (error) {
            console.error('Failed to upload code files:', error);
            throw error;
        }
    }

    /**
     * الحصول على جميع ملفات الكود لمشروع معين
     * GET /api/upm/projects/{projectId}/artifacts/
     */
    static async getProjectCodeFiles(projectId: string): Promise<CodeFile[]> {
        try {
            const response = await apiClient.get<CodeFile[]>(
                `api/upm/projects/${projectId}/artifacts/`
            );
            return response.data;
        } catch (error) {
            console.error('Failed to fetch project code files:', error);
            throw error;
        }
    }

    /**
     * الحصول على تفاصيل ملف كود معين
     * GET /api/codefiles/{id}/
     */
    static async getCodeFileDetail(codeFileId: string): Promise<CodeFile> {
        try {
            const response = await apiClient.get<CodeFile>(
                API_ENDPOINTS.analysis.codefileDetail(codeFileId)
            );
            return response.data;
        } catch (error) {
            console.error('Failed to fetch code file details:', error);
            throw error;
        }
    }

    /**
     * بدء عملية تحليل لملف كود
     * POST /api/analyze/
     * Body: { code_file_id: string, analysis_type: 'class_diagram' | 'explanation' }
     */
    static async startAnalysis(
        codeFileId: string,
        analysisType: 'class_diagram' | 'explanation' = 'class_diagram',
        explanationLevel?: 'high' | 'low'
    ): Promise<AnalysisStartResponse> {
        try {
            const body: any = {
                code_file_id: codeFileId,
                analysis_type: analysisType,
            };

            if (analysisType === 'explanation' && explanationLevel) {
                body.explanation_level = explanationLevel;
            }

            const response = await apiClient.post<AnalysisStartResponse>(
                API_ENDPOINTS.analysis.analyze(),
                body
            );
            return response.data;
        } catch (error) {
            console.error('Failed to start analysis:', error);
            throw error;
        }
    }

    /**
     * الحصول على نتائج التحليل
     * GET /api/analysis-results/?code_file_id={code_file_id}
     */
    static async getAnalysisResults(codeFileId?: string): Promise<any[]> {
        try {
            const url = codeFileId
                ? `${API_ENDPOINTS.analysis.results()}?code_file_id=${codeFileId}`
                : API_ENDPOINTS.analysis.results();

            const response = await apiClient.get<{ results: any[] }>(url);
            return response.data.results || response.data;
        } catch (error) {
            console.error('Failed to fetch analysis results:', error);
            throw error;
        }
    }

    /**
     * الحصول على نتيجة تحليل معينة
     * GET /api/analysis-results/{id}/
     */
    static async getAnalysisResultDetail(resultId: string): Promise<any> {
        try {
            const response = await apiClient.get(
                API_ENDPOINTS.analysis.result(resultId)
            );
            return response.data;
        } catch (error) {
            console.error('Failed to fetch analysis result detail:', error);
            throw error;
        }
    }

    /**
     * الحصول على حالة مهمة معينة
     * GET /api/task-status/{task_id}/
     */
    static async getTaskStatus(taskId: string): Promise<any> {
        try {
            const response = await apiClient.get(
                API_ENDPOINTS.analysis.taskStatus(taskId)
            );
            return response.data;
        } catch (error) {
            console.error('Failed to fetch task status:', error);
            throw error;
        }
    }

    /**
     * حذف ملف كود
     * DELETE /api/codefiles/{id}/
     */
    static async deleteCodeFile(codeFileId: string): Promise<void> {
        try {
            await apiClient.delete(
                API_ENDPOINTS.analysis.codefileDetail(codeFileId)
            );
        } catch (error) {
            console.error('Failed to delete code file:', error);
            throw error;
        }
    }

    /**
     * تحديث ملف كود
     * PUT /api/codefiles/{id}/
     */
    static async updateCodeFile(
        codeFileId: string,
        data: Partial<CodeFile>
    ): Promise<CodeFile> {
        try {
            const response = await apiClient.put<CodeFile>(
                API_ENDPOINTS.analysis.codefileDetail(codeFileId),
                data
            );
            return response.data;
        } catch (error) {
            console.error('Failed to update code file:', error);
            throw error;
        }
    }
}

export default FilesService;