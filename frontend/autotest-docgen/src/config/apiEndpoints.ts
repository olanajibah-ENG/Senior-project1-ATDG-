/**
 * Enhanced API Endpoints Configuration
 * Centralized endpoint definitions with validation and error handling
 */

import { API_ENDPOINTS } from './api.config';

/**
 * Validates and constructs API endpoints with proper error handling
 */
export class EndpointValidator {
  /**
   * Validate endpoint URL format
   */
  static validateEndpoint(endpoint: string): boolean {
    try {
      const url = new URL(endpoint, 'http://localhost:80');
      return url.pathname.startsWith('/api/');
    } catch {
      return false;
    }
  }

  /**
   * Get endpoint with validation and logging
   */
  static getEndpoint(name: string, endpointFn: () => string): string {
    try {
      const endpoint = endpointFn();
      
      if (!this.validateEndpoint(endpoint)) {
        console.error(`❌ Invalid endpoint format for ${name}:`, endpoint);
        throw new Error(`Invalid endpoint format: ${endpoint}`);
      }

      console.log(`✅ Endpoint validated for ${name}:`, endpoint);
      return endpoint;
    } catch (error) {
      console.error(`💥 Failed to construct endpoint ${name}:`, error);
      throw error;
    }
  }
}

/**
 * Enhanced API endpoints with validation
 */
export const VALIDATED_ENDPOINTS = {
  // Auth endpoints
  auth: {
    login: () => EndpointValidator.getEndpoint('auth.login', API_ENDPOINTS.auth.login),
    signup: () => EndpointValidator.getEndpoint('auth.signup', API_ENDPOINTS.auth.signup),
    refreshToken: () => EndpointValidator.getEndpoint('auth.refreshToken', API_ENDPOINTS.auth.refreshToken),
    verifyToken: () => EndpointValidator.getEndpoint('auth.verifyToken', API_ENDPOINTS.auth.verifyToken),
    deleteAccount: () => EndpointValidator.getEndpoint('auth.deleteAccount', API_ENDPOINTS.auth.deleteAccount),
  },

  // Projects endpoints
  projects: {
    list: () => EndpointValidator.getEndpoint('projects.list', API_ENDPOINTS.projects.list),
    create: () => EndpointValidator.getEndpoint('projects.create', API_ENDPOINTS.projects.create),
    detail: (id: string) => {
      const endpoint = API_ENDPOINTS.projects.detail(id);
      return EndpointValidator.getEndpoint(`projects.detail(${id})`, () => endpoint);
    },
    artifacts: (projectId: string) => {
      const endpoint = API_ENDPOINTS.projects.artifacts(projectId);
      return EndpointValidator.getEndpoint(`projects.artifacts(${projectId})`, () => endpoint);
    },
  },

  // Analysis endpoints (Fixed paths)
  analysis: {
    // Code Files
    codefiles: () => EndpointValidator.getEndpoint('analysis.codefiles', API_ENDPOINTS.analysis.codefiles),
    codefileDetail: (id: string) => {
      const endpoint = API_ENDPOINTS.analysis.codefileDetail(id);
      return EndpointValidator.getEndpoint(`analysis.codefileDetail(${id})`, () => endpoint);
    },
    codefileAnalyze: (id: string) => {
      const endpoint = API_ENDPOINTS.analysis.codefileAnalyze(id);
      return EndpointValidator.getEndpoint(`analysis.codefileAnalyze(${id})`, () => endpoint);
    },
    codefilesByProject: (projectId: string) => {
      const endpoint = API_ENDPOINTS.analysis.codefilesByProject(projectId);
      return EndpointValidator.getEndpoint(`analysis.codefilesByProject(${projectId})`, () => endpoint);
    },

    // Analysis Workflow
    analyze: () => EndpointValidator.getEndpoint('analysis.analyze', API_ENDPOINTS.analysis.analyze),

    // Analysis Jobs
    jobs: () => EndpointValidator.getEndpoint('analysis.jobs', API_ENDPOINTS.analysis.jobs),
    jobDetail: (id: string) => {
      const endpoint = API_ENDPOINTS.analysis.jobDetail(id);
      return EndpointValidator.getEndpoint(`analysis.jobDetail(${id})`, () => endpoint);
    },

    // Analysis Results (Fixed - ensure proper path)
    results: () => {
      // This should be /api/analysis/analysis-results/ not /api/analysis-results/
      const endpoint = API_ENDPOINTS.analysis.results();
      console.log('🔍 Analysis results endpoint:', endpoint);
      return EndpointValidator.getEndpoint('analysis.results', () => endpoint);
    },
    result: (id: string) => {
      const endpoint = API_ENDPOINTS.analysis.result(id);
      return EndpointValidator.getEndpoint(`analysis.result(${id})`, () => endpoint);
    },
    taskStatus: (taskId: string) => {
      const endpoint = API_ENDPOINTS.analysis.taskStatus(taskId);
      return EndpointValidator.getEndpoint(`analysis.taskStatus(${taskId})`, () => endpoint);
    },
    classDiagram: (id: string) => {
      const endpoint = API_ENDPOINTS.analysis.classDiagram(id);
      return EndpointValidator.getEndpoint(`analysis.classDiagram(${id})`, () => endpoint);
    },

    // Export & Documentation
    export: (analysisId: string) => {
      const endpoint = API_ENDPOINTS.analysis.export(analysisId);
      return EndpointValidator.getEndpoint(`analysis.export(${analysisId})`, () => endpoint);
    },
    generatedFiles: () => EndpointValidator.getEndpoint('analysis.generatedFiles', API_ENDPOINTS.analysis.generatedFiles),
    downloadGeneratedFile: (fileId: string) => {
      const endpoint = API_ENDPOINTS.analysis.downloadGeneratedFile(fileId);
      return EndpointValidator.getEndpoint(`analysis.downloadGeneratedFile(${fileId})`, () => endpoint);
    },
    saveArtifact: () => EndpointValidator.getEndpoint('analysis.saveArtifact', API_ENDPOINTS.analysis.saveArtifact),
    getProjectArtifacts: (projectId: string) => {
      const endpoint = API_ENDPOINTS.analysis.getProjectArtifacts(projectId);
      return EndpointValidator.getEndpoint(`analysis.getProjectArtifacts(${projectId})`, () => endpoint);
    },
    updateArtifact: (artifactId: string) => {
      const endpoint = API_ENDPOINTS.analysis.updateArtifact(artifactId);
      return EndpointValidator.getEndpoint(`analysis.updateArtifact(${artifactId})`, () => endpoint);
    },
    generateDocument: () => EndpointValidator.getEndpoint('analysis.generateDocument', API_ENDPOINTS.analysis.generateDocument),

    // AI Explanations
    aiExplanations: () => EndpointValidator.getEndpoint('analysis.aiExplanations', API_ENDPOINTS.analysis.aiExplanations),
    generateExplanation: () => EndpointValidator.getEndpoint('analysis.generateExplanation', API_ENDPOINTS.analysis.generateExplanation),
    explanationTaskStatus: (taskId: string) => {
      const endpoint = API_ENDPOINTS.analysis.explanationTaskStatus(taskId);
      return EndpointValidator.getEndpoint(`analysis.explanationTaskStatus(${taskId})`, () => endpoint);
    },
    explanationAnalysisTasks: (analysisId: string) => {
      const endpoint = API_ENDPOINTS.analysis.explanationAnalysisTasks(analysisId);
      return EndpointValidator.getEndpoint(`analysis.explanationAnalysisTasks(${analysisId})`, () => endpoint);
    },
    exportLegacy: () => EndpointValidator.getEndpoint('analysis.exportLegacy', API_ENDPOINTS.analysis.exportLegacy),
  },

  // Notifications endpoints (Fixed - ensure proper path)
  notifications: {
    // Notification types - for creating notifications
    project: () => EndpointValidator.getEndpoint('notifications.project', API_ENDPOINTS.notifications.project),
    code: () => EndpointValidator.getEndpoint('notifications.code', API_ENDPOINTS.notifications.code),
    documentation: () => EndpointValidator.getEndpoint('notifications.documentation', API_ENDPOINTS.notifications.documentation),
    user: () => EndpointValidator.getEndpoint('notifications.user', API_ENDPOINTS.notifications.user),
    system: () => EndpointValidator.getEndpoint('notifications.system', API_ENDPOINTS.notifications.system),
    custom: () => EndpointValidator.getEndpoint('notifications.custom', API_ENDPOINTS.notifications.custom),
    settings: () => EndpointValidator.getEndpoint('notifications.settings', API_ENDPOINTS.notifications.settings),

    // Notification management (Fixed - ensure proper path)
    list: () => {
      // This should be /api/notifications/ not /api/?user_id=...
      const endpoint = API_ENDPOINTS.notifications.list();
      console.log('🔍 Notifications list endpoint:', endpoint);
      return EndpointValidator.getEndpoint('notifications.list', () => endpoint);
    },
    stats: () => EndpointValidator.getEndpoint('notifications.stats', API_ENDPOINTS.notifications.stats),
    markAllRead: () => EndpointValidator.getEndpoint('notifications.markAllRead', API_ENDPOINTS.notifications.markAllRead),
    detail: (id: string) => {
      const endpoint = API_ENDPOINTS.notifications.detail(id);
      return EndpointValidator.getEndpoint(`notifications.detail(${id})`, () => endpoint);
    },
    markRead: (id: string) => {
      const endpoint = API_ENDPOINTS.notifications.markRead(id);
      return EndpointValidator.getEndpoint(`notifications.markRead(${id})`, () => endpoint);
    },
    delete: (id: string) => {
      const endpoint = API_ENDPOINTS.notifications.delete(id);
      return EndpointValidator.getEndpoint(`notifications.delete(${id})`, () => endpoint);
    },
  },

  // Logic Explanation endpoints
  logicExplanation: {
    levels: () => EndpointValidator.getEndpoint('logicExplanation.levels', API_ENDPOINTS.logicExplanation.levels),
    explain: () => EndpointValidator.getEndpoint('logicExplanation.explain', API_ENDPOINTS.logicExplanation.explain),
    projectFiles: (projectId: string) => {
      const endpoint = API_ENDPOINTS.logicExplanation.projectFiles(projectId);
      return EndpointValidator.getEndpoint(`logicExplanation.projectFiles(${projectId})`, () => endpoint);
    },
  },

  // Health check
  health: () => {
    const endpoint = API_ENDPOINTS.health();
    console.log('🔍 Health check endpoint:', endpoint);
    return endpoint;
  },
} as const;

/**
 * Helper function to get all endpoints for debugging
 */
export function debugEndpoints() {
  console.group('🔍 API Endpoints Debug');
  
  Object.entries(VALIDATED_ENDPOINTS).forEach(([category, endpoints]) => {
    console.group(`📁 ${category}`);
    
    Object.entries(endpoints).forEach(([name, endpointFn]) => {
      try {
        if (typeof endpointFn === 'function') {
          // Skip functions that require parameters
          if (endpointFn.toString().includes('id') || endpointFn.toString().includes('projectId')) {
            console.log(`⚙️ ${name}: requires parameters`);
          } else {
            const endpoint = endpointFn();
            console.log(`✅ ${name}: ${endpoint}`);
          }
        }
      } catch (error) {
        console.error(`❌ ${name}:`, error);
      }
    });
    
    console.groupEnd();
  });
  
  console.groupEnd();
}

/**
 * Check if all critical endpoints are accessible
 */
export async function validateCriticalEndpoints() {
  const criticalEndpoints = [
    { name: 'auth.login', fn: VALIDATED_ENDPOINTS.auth.login },
    { name: 'projects.list', fn: VALIDATED_ENDPOINTS.projects.list },
    { name: 'notifications.list', fn: VALIDATED_ENDPOINTS.notifications.list },
    { name: 'analysis.results', fn: VALIDATED_ENDPOINTS.analysis.results },
  ];

  const results: { name: string; valid: boolean; endpoint: string; error?: string }[] = [];

  for (const { name, fn } of criticalEndpoints) {
    try {
      const endpoint = fn();
      results.push({ name, valid: true, endpoint });
    } catch (error) {
      results.push({ 
        name, 
        valid: false, 
        endpoint: 'unknown', 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  console.table(results);
  return results;
}
