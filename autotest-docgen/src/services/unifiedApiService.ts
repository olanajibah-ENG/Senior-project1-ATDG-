/**
 * Unified API Service - replaces direct fetch calls with consistent axios usage
 * Uses the same apiClient configuration for all requests
 */

import apiClient from './apiClient';

// Helper: format file size for logging
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

class UnifiedApiService {
  /**
   * Generate class diagram for a code file
   * This is the specific fix for the 404 errors in DocumentGenerationPage
   */
  static async generateClassDiagram(codeFileId: string, projectId: string) {
    try {
      console.log('🎯 Generating class diagram with unified API service');
      console.log(`📁 Code File ID: ${codeFileId}`);
      console.log(`🏗️ Project ID: ${projectId}`);

      // Use the correct endpoint that works in Postman
      const response = await apiClient.post('/api/analysis/analyze/', {
        code_file_id: codeFileId,
        analysis_type: 'class_diagram'
      });

      console.log('✅ Class diagram generation started:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to generate class diagram:', error);
      throw error;
    }
  }

  /**
   * Save artifact to backend
   */
  static async saveArtifact(artifactData: any) {
    try {
      const formData = new FormData();
      formData.append('file', artifactData.file);
      if (artifactData.filename) formData.append('filename', artifactData.filename);
      if (artifactData.projectId) formData.append('project_id', artifactData.projectId);

      const response = await apiClient.post('/api/analysis/codefiles/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      return response.data;
    } catch (error) {
      console.error('❌ Failed to save artifact:', error);
      throw error;
    }
  }


  /**
   * Get project artifacts
   */
  static async getProjectArtifacts(projectId: string, filters?: any) {
    try {
      const params = new URLSearchParams();
      params.append('project_id', projectId);

      if (filters?.file_id) params.append('file_id', filters.file_id);
      if (filters?.artifact_type) params.append('artifact_type', filters.artifact_type);

      const response = await apiClient.get(`/api/analysis/analysis-results/?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get project artifacts:', error);
      throw error;
    }
  }

  /**
   * Update existing artifact
   */
  static async updateArtifact(artifactId: string, updateData: any) {
    try {
      const response = await apiClient.put(`/api/analysis/codefiles/${artifactId}/`, updateData);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to update artifact:', error);
      throw error;
    }
  }

  /**
   * Get analysis results
   */
  static async getAnalysisResults(codeFileId?: string) {
    try {
      const url = codeFileId
        ? `/api/analysis/analysis-results/?code_file_id=${codeFileId}`
        : '/api/analysis/analysis-results/';

      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get analysis results:', error);
      throw error;
    }
  }

  /**
   * Export analysis result
   */
  static async exportAnalysis(analysisId: string, params: {
    format?: 'pdf' | 'md' | 'html' | 'xml';
    type?: 'high' | 'low' | 'high_level' | 'low_level' | 'detailed';
    mode?: 'display' | 'download';
  } = {}) {
    try {
      // URL: /api/analysis/export/{id}/?format=...&type=...
      // export_doc view handles both ObjectId (file) and project UUID
      const queryParams = new URLSearchParams(params as any).toString();
      const url = `/api/analysis/export/${analysisId}/?${queryParams}`;

      console.log('🔗 Export URL:', url);
      console.log('📤 Export params:', params);

      const response = await apiClient.get(url, {
        responseType: 'blob'
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', response.headers);
      console.log('📦 Blob type:', response.data.type);
      console.log('📦 Blob size:', response.data.size);

      // Validate blob for PDF
      if (params.format === 'pdf') {
        const arrayBuffer = await response.data.slice(0, 4).arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        const header = String.fromCharCode.apply(null, Array.from(uint8Array));
        console.log('🔍 File header:', header);

        if (header !== '%PDF') {
          console.error('❌ Server did not return a valid PDF file');
          console.error('❌ File header:', header);
          console.error('❌ Expected: %PDF');
          throw new Error('Server returned invalid PDF file. The backend might be returning Python code instead of PDF.');
        }
      }

      return response.data;
    } catch (error) {
      console.error('❌ Failed to export analysis:', error);
      throw error;
    }
  }

  /**
   * Download generated file
   */
  static async downloadGeneratedFile(fileId: string) {
    try {
      const response = await apiClient.get(`/api/analysis/download-generated-file/${fileId}/`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('❌ Failed to download generated file:', error);
      throw error;
    }
  }

  /**
   * رفع ZIP/مجلد كامل للمشروع
   * POST /api/upm/projects/{project_id}/folder-upload/
   */
  static async folderUpload(projectId: string, zipFile: File) {
    try {
      console.log('📁 Uploading folder/ZIP for project:', projectId);
      console.log('📦 ZIP file:', zipFile.name, formatFileSize(zipFile.size));

      const formData = new FormData();
      formData.append('file', zipFile);

      // Don't set Content-Type — axios will set multipart/form-data with boundary automatically
      const response = await apiClient.post(
        `/api/upm/projects/${projectId}/folder-upload/`,
        formData,
        {
          headers: { 'Content-Type': undefined },
          timeout: 120000, // 2 minutes for large ZIP files
          onUploadProgress: (progressEvent) => {
            const percent = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            console.log(`📤 Upload progress: ${percent}%`);
          },
        }
      );

      console.log('✅ Folder uploaded successfully:', response.data);
      return response.data; // { project_id, project_name, version, file_count, file_ids, files }
    } catch (error) {
      console.error('❌ Failed to upload folder:', error);
      throw error;
    }
  }

  /**
   * بدء تحليل مشروع كامل
   * POST /api/analysis/analyze-project/
   */
  static async analyzeProject(projectId: string) {
    try {
      console.log('🔬 Starting project analysis for:', projectId);

      const response = await apiClient.post('/api/analysis/analyze-project/', { project_id: projectId });

      console.log('✅ Project analysis started:', response.data);
      return response.data; // { message, project_id, task_id }
    } catch (error) {
      console.error('❌ Failed to start project analysis:', error);
      throw error;
    }
  }

  /**
   * الحصول على حالة تحليل المشروع
   * GET /api/analysis/analyze-project/?project_id={id}
   */
  static async getAnalyzeProjectStatus(projectId: string) {
    try {
      const response = await apiClient.get(`/api/analysis/analyze-project/?project_id=${projectId}`);
      return response.data;
      // { _id, project_id, status: "COMPLETED"|"IN_PROGRESS"|"FAILED", analysis_ids, dependency_graph, contexts }
    } catch (error) {
      console.error('❌ Failed to get project status:', error);
      throw error;
    }
  }

  /**
   * الحصول على class diagram للمشروع الكامل
   * GET /api/analysis/project-class-diagram/{project_id}/
   */
  static async getProjectClassDiagram(projectId: string) {
    try {
      console.log('📊 Fetching project class diagram for:', projectId);

      const response = await apiClient.get(`/api/analysis/project-class-diagram/${projectId}/`);

      console.log('✅ Project class diagram fetched:', response.data);
      return response.data;
      // { project_id, status, total_classes, project_class_diagram: { classes, relationships } }
    } catch (error) {
      console.error('❌ Failed to get project class diagram:', error);
      throw error;
    }
  }

  /**
   * توليد شرح AI للكود (high_level أو low_level)
   * POST /api/analysis/ai-explanations/generate-explanation/
   */
  static async generateExplanation(analysisId: string, type: 'high_level' | 'low_level') {
    try {
      console.log('🤖 Generating explanation:', { analysisId, type });

      const response = await apiClient.post('/api/analysis/ai-explanations/generate-explanation/', {
        analysis_id: analysisId,
        type,
      });

      console.log('✅ Explanation task started:', response.data);
      return response.data; // { task_id, status, message, analysis_id, type }
    } catch (error) {
      console.error('❌ Failed to generate explanation:', error);
      throw error;
    }
  }

  /**
   * فحص حالة مهمة الشرح
   * GET /api/analysis/ai-explanations/task-status/?task_id={id}
   */
  static async getExplanationTaskStatus(taskId: string) {
    try {
      const response = await apiClient.get(`/api/analysis/ai-explanations/task-status/?task_id=${taskId}`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get explanation task status:', error);
      throw error;
    }
  }

  /**
   * تصدير الوثيقة (PDF أو Markdown)
   * GET /api/analysis/export/{analysis_id}/?format=pdf|md&type=low_level|high_level&mode=download|display
   * يستخدم analysis_id الخاص بالشرح المولد
   */
  static async exportDocument(analysisId: string, params: {
    format: 'pdf' | 'md';
    type: 'low_level' | 'high_level';
    mode: 'download' | 'display';
  }) {
    try {
      console.log('📄 Exporting document:', { analysisId, ...params });

      const queryString = new URLSearchParams(params as any).toString();
      const response = await apiClient.get(`/api/analysis/export/${analysisId}/?${queryString}`, {
        responseType: 'blob',
      });

      console.log('✅ Document exported, size:', response.data.size);
      return response.data as Blob;
    } catch (error) {
      console.error('❌ Failed to export document:', error);
      throw error;
    }
  }

  /**
   * Upload files with project_id (existing single-file flow)
   */
  static async uploadFilesWithProject(data: {
    files: File[];
    project_id: string;
    language: string;
    version: string;
    codeName?: string;
    githubUrl?: string;
    zipFile?: File;
  }) {
    try {
      const formData = new FormData();

      // Upload each file separately with required fields
      // Backend requires: filename, file_type per file
      if (data.files.length === 1) {
        const file = data.files[0];
        formData.append('uploaded_file', file);
        formData.append('filename', file.name);
        formData.append('file_type', file.name.split('.').pop()?.toLowerCase() || 'py');
        formData.append('project_id', data.project_id);
        formData.append('language', data.language || 'auto-detect');
        formData.append('version', data.version || '');
        if (data.codeName) formData.append('code_name', data.codeName);

        const response = await apiClient.post('/api/analysis/codefiles/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
      }

      // Multiple files — upload one by one
      const results = [];
      for (const file of data.files) {
        const fd = new FormData();
        fd.append('uploaded_file', file);
        fd.append('filename', file.name);
        fd.append('file_type', file.name.split('.').pop()?.toLowerCase() || 'py');
        fd.append('project_id', data.project_id);
        fd.append('language', data.language || 'auto-detect');
        fd.append('version', data.version || '');
        if (data.codeName) fd.append('code_name', data.codeName);

        const response = await apiClient.post('/api/analysis/codefiles/', fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        results.push(response.data);
      }
      return results;
    } catch (error) {
      console.error('❌ Failed to upload files:', error);
      throw error;
    }
  }

  /**
   * ربط مشروع بمستودع GitHub
   * POST /api/upm/projects/{projectId}/github/connect/
   */
  static async connectGithubRepo(projectId: string, data: {
    repo_url: string;
    branch: string;
    github_token?: string;
  }) {
    try {
      console.log('🔗 Connecting GitHub repo for project:', projectId);
      const response = await apiClient.post(
        `/api/upm/projects/${projectId}/github/connect/`,
        data
      );
      console.log('✅ GitHub repo connected:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to connect GitHub repo:', error);
      throw error;
    }
  }

  /**
   * Get generated files for specific project
   */
  static async getProjectGeneratedFiles(projectId: string) {
    try {
      const response = await apiClient.get(`/api/analysis/generated-files/?project_id=${projectId}`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get project generated files:', error);
      throw error;
    }
  }

}

export default UnifiedApiService;
