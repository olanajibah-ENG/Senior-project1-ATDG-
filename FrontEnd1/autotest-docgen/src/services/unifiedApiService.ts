/**
 * Unified API Service - replaces direct fetch calls with consistent axios usage
 * Uses the same apiClient configuration for all requests
 */

import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api.config';

// Helper function to get auth headers (same as used in DocumentGenerationPage)
const getAuthHeaders = (url?: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add CSRF token for Django
  const getCookie = (name: string) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift();
    }
    return null;
  };

  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }

  // Always add Authorization for AI endpoints
  const isAiEndpoint = url?.includes('/api/analysis/ai-explanations/') ||
    url?.includes('/api/analysis/');

  // Get token from localStorage
  const token = localStorage.getItem('access_token');

  if (token && (isAiEndpoint || !url?.includes('/login/') && !url?.includes('/signup/') && !url?.includes('/token/'))) {
    headers['Authorization'] = `Bearer ${token}`;
    console.log('🔑 getAuthHeaders: Added Authorization header for:', url);
  } else if (!token) {
    console.warn('⚠️ getAuthHeaders: No access token found in localStorage for:', url);
  }

  return headers;
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
   * Get generated files list
   */
  static async getGeneratedFiles() {
    try {
      const response = await apiClient.get('/api/analysis/generated-files/');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get generated files:', error);
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
      const response = await apiClient.get(`/api/analysis/export/${analysisId}/?${queryString}`, {
        responseType: 'blob'
      });
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
   * Generate AI Explanation
   * POST /api/analysis/ai-explanations/generate-explanation/
   */
  static async generateAIExplanation(analysisId: string, expType: 'high' | 'low') {
    try {
      console.log('🎯 Generating AI explanation with unified API service');
      console.log(`📁 Analysis ID: ${analysisId}`);
      console.log(`🎯 Explanation Type: ${expType}`);

      // Use the API config to build the correct URL
      const url = API_ENDPOINTS.analysis.generateExplanation();
      console.log('🔗 Using URL:', url);

      const response = await apiClient.post(url, {
        analysis_id: analysisId,
        exp_type: expType // backend expects 'high' or 'low'
      });

      console.log('✅ AI explanation generation started:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to generate AI explanation:', error);
      throw error;
    }
  }

  /**
   * Get AI Explanation Task Status
   * GET /api/analysis/ai-explanations/task-status/?task_id={task_id}
   */
  static async getExplanationTaskStatus(taskId: string) {
    try {
      console.log('🔍 Checking AI explanation task status:', taskId);

      const response = await apiClient.get(`/api/analysis/ai-explanations/task-status/?task_id=${taskId}`);
      console.log('✅ Task status response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get explanation task status:', error);
      throw error;
    }
  }

  /**
   * Get AI Explanation by ID
   * GET /api/analysis/ai-explanations/{id}/
   */
  static async getAIExplanationById(explanationId: string) {
    try {
      console.log('🔍 Fetching AI explanation:', explanationId);

      const response = await apiClient.get(`/api/analysis/ai-explanations/${explanationId}/`);
      console.log('✅ AI explanation response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get AI explanation:', error);
      throw error;
    }
  }
}

export default UnifiedApiService;
