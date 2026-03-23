/**
 * Unified API Service - replaces direct fetch calls with consistent axios usage
 * Uses the same apiClient configuration for all requests
 */

import apiClient from './apiClient';

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
    format?: 'pdf' | 'md';
    type?: 'high' | 'low' | 'detailed';
    mode?: 'display' | 'download';
  } = {}) {
    try {
      const queryString = new URLSearchParams(params as any).toString();
      const url = `/api/analysis/export/${analysisId}/?${queryString}`;

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
   * Upload files with project_id
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

      // Add files
      data.files.forEach((file) => {
        formData.append(`files`, file);
      });

      // Add other fields
      formData.append('project_id', data.project_id);
      formData.append('language', data.language);
      formData.append('version', data.version);

      if (data.codeName) {
        formData.append('code_name', data.codeName);
      }

      if (data.githubUrl) {
        formData.append('github_url', data.githubUrl);
      }

      if (data.zipFile) {
        formData.append('zip_file', data.zipFile);
      }

      const response = await apiClient.post('/api/analysis/codefiles/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      return response.data;
    } catch (error) {
      console.error('❌ Failed to upload files:', error);
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
