/**
 * Extended API Service - Additional methods for specific functionality
 * Works alongside UnifiedApiService
 */

import apiClient from './apiClient';

// Types
export interface DependencyGraph {
  nodes: Array<{
    id: string;
    name: string;
    type: string;
    language?: string;
    file_path?: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    type: string;
    strength?: number;
  }>;
  metadata?: {
    total_files?: number;
    total_dependencies?: number;
    complexity_score?: number;
  };
}

export interface CrossFileContext {
  fileContexts: Array<{
    fileName: string;
    context: string;
    imports: string[];
    exports: string[];
  }>;
  file_relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
}

export interface AIExplanationRequest {
  code_snippet: string;
  question?: string;
  language?: string;
  context?: string;
  analysis_id?: string;
}

export interface ExplanationEvaluationRequest {
  explanation_id?: string;
  rating: number;
  feedback: string;
  helpful?: boolean;
  clarity?: number;
  accuracy?: number;
}

export interface HumanReviewRequest {
  analysis_id: string;
  review_data: {
    approved: boolean;
    comments: string;
    suggestions: any[];
  };
}

export interface ReviewerStats {
  totalReviews: number;
  pendingReviews: number;
  completedReviews: number;
  averageScore: number;
  recentActivity: Array<{
    date: string;
    action: string;
    analysisId: string;
  }>;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role_type: string;
  is_active: boolean;
  is_online: boolean;
  last_seen: string;
  date_joined: string;
  project_count: number;
}

export interface OnlineUser {
  username: string;
  full_name: string;
  role_type: string;
  last_seen: string;
}

export interface CreateReviewerRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

class ExtendedApiService {
  /**
   * Get dependency graph for project files
   */
  static async getDependencyGraph(projectId: string, fileNames: string[]): Promise<DependencyGraph> {
    try {
      const response = await apiClient.post('/api/analysis/dependency-graph/', {
        project_id: projectId,
        file_names: fileNames
      });
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get dependency graph:', error);
      throw error;
    }
  }

  /**
   * Get cross-file context analysis
   */
  static async getCrossFileContext(projectId: string, fileNames: string[]): Promise<CrossFileContext> {
    try {
      const response = await apiClient.post('/api/analysis/cross-file-context/', {
        project_id: projectId,
        file_names: fileNames
      });
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get cross-file context:', error);
      throw error;
    }
  }

  /**
   * Get AI explanations
   */
  static async getAIExplanations() {
    try {
      const response = await apiClient.get('/api/analysis/ai-explanations/');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get AI explanations:', error);
      throw error;
    }
  }

  /**
   * Request AI explanation for code snippet
   */
  static async requestAIExplanation(request: AIExplanationRequest) {
    try {
      const response = await apiClient.post('/api/analysis/ai-explanations/', request);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to request AI explanation:', error);
      throw error;
    }
  }

  /**
   * Export analysis in specified format
   */
  static async exportAnalysis(analysisId: string, format: 'pdf' | 'markdown') {
    try {
      const response = await apiClient.get(`/api/analysis/export/${analysisId}/`, {
        params: { format },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('❌ Failed to export analysis:', error);
      throw error;
    }
  }

  /**
   * Evaluate an AI explanation
   */
  static async evaluateExplanation(explanationId: string, evaluation: ExplanationEvaluationRequest) {
    try {
      const response = await apiClient.post(`/api/analysis/evaluate-explanation/${explanationId}/`, evaluation);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to evaluate explanation:', error);
      throw error;
    }
  }

  /**
   * Get evaluation history for an explanation
   */
  static async getEvaluationHistory(explanationId: string) {
    try {
      const response = await apiClient.get(`/api/analysis/evaluation-history/${explanationId}/`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get evaluation history:', error);
      throw error;
    }
  }

  /**
   * Submit human review for analysis
   */
  static async submitHumanReview(analysisId: string, review: HumanReviewRequest) {
    try {
      const response = await apiClient.post(`/api/analysis/submit-human-review/${analysisId}/`, {
        ...review,
        analysis_id: analysisId
      });
      return response.data;
    } catch (error) {
      console.error('❌ Failed to submit human review:', error);
      throw error;
    }
  }

  /**
   * Notify admin about something
   */
  static async notifyAdmin(notification: {
    message: string;
    type: 'info' | 'warning' | 'error';
    analysis_id: string;
  }) {
    try {
      const response = await apiClient.post('/api/upm/reviewer/notify-admin/', notification);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to notify admin:', error);
      throw error;
    }
  }

  /**
   * Get admin users
   */
  static async getAdminUsers(): Promise<AdminUser[]> {
    try {
      const response = await apiClient.get('/api/upm/admin/users/');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get admin users:', error);
      throw error;
    }
  }

  /**
   * Create a new reviewer
   */
  static async createReviewer(reviewerData: CreateReviewerRequest): Promise<AdminUser> {
    try {
      const response = await apiClient.post('/api/upm/admin/users/create-reviewer/', reviewerData);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to create reviewer:', error);
      throw error;
    }
  }

  /**
   * Toggle user active status
   */
  static async toggleUserActive(userId: number): Promise<void> {
    try {
      await apiClient.patch(`/api/upm/admin/users/${userId}/toggle-active/`);
    } catch (error) {
      console.error('❌ Failed to toggle user active status:', error);
      throw error;
    }
  }

  /**
   * Get online users
   */
  static async getOnlineUsers(): Promise<OnlineUser[]> {
    const response = await apiClient.get('/api/upm/users/online/');
    return response.data.users || [];  // ✅
  }
}

export default ExtendedApiService;
