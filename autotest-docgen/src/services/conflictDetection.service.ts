/**
 * Conflict Detection Service — Full Real API Integration
 *
 * Endpoints covered:
 *   GET  /api/upm/projects/                           — list projects ✅
 *   GET  /api/upm/projects/{project_id}/tree/         — list project files (FIXED!) ✅ NEW
 *   GET  /api/analysis/file-versions/{file_id}/       — list file versions ✅
 *   GET  /api/analysis/file-docs/{file_id}/           — list docs linked to file ✅
 *   POST /api/analysis/upload-folder/                  — upload ZIP version ✅
 *   POST /api/analysis/detect-conflict/                — start analysis ✅
 *   GET  /api/analysis/conflict-status/?task_id=       — poll task ✅
 *   GET  /api/analysis/conflict-result/{id}/           — fetch result ✅
 *
 * 🔧 FIXED: Changed from /api/analysis/codefiles/?project_id= to /api/upm/projects/{id}/tree/
 *           This ensures only files from the selected project are returned (not all files from all projects)
 */

import apiClient from './apiClient';
import { API_CONFIG } from '../config/api.config';

const ai  = (path: string) => `${API_CONFIG.PREFIX.AI}/${path}`;
const upm = (path: string) => `${API_CONFIG.PREFIX.UPM}/${path}`;

// ================================================================
// Types — Project (from UPM)
// ================================================================
export interface UpmProject {
  id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
  username?: string;
}

// ================================================================
// Types — Project Code File
// ================================================================
export interface ProjectFile {
  file_id: string;
  filename: string;
  filepath: string;
  /** versions_count may be returned depending on backend */
  versions_count?: number;
  has_documentation?: boolean;
}

// ================================================================
// Types — File Versions
// ================================================================
export interface FileVersion {
  version_id: string;
  version_number: string;   // e.g. "v1", "v2"
  status?: string;          // "unchanged" | "modified" | ...
  file_id: string;
  filename?: string;
  filepath?: string;
  created_at: string;
  is_latest?: boolean;
}

export interface FileVersionsResponse {
  success: boolean;
  file_id: string;
  filename: string;
  filepath: string;
  project_id: string;
  total_versions: number;
  history: FileVersion[];
}

// ================================================================
// Types — File Documentation
// ================================================================
export interface FileDoc {
  doc_id: string;
  explanation_type: 'high_level' | 'low_level' | 'detailed' | string;
  analysis_id?: string;
  created_at: string;
  content_preview?: string;
  /** relevance score 0-1 for matching to versions */
  relevance_score?: number;
  linked_to_version?: string;
  file_name?: string;
}

export interface FileDocsResponse {
  success: boolean;
  file_id: string;
  filename: string;
  filepath: string;
  total_docs: number;
  docs: FileDoc[];
}

// ================================================================
// Types — Upload Folder
// ================================================================
export interface UploadFolderFile {
  file_id: string;
  filename: string;
  filepath: string;
}

export interface UploadFolderVersion {
  project_id: string;
  project_name: string;
  version_number: number;
  file_count: number;
  file_ids: string[];
  files: UploadFolderFile[];
}

// ================================================================
// Types — Detect Conflict
// ================================================================
export interface DetectConflictPayload {
  analysis_type: 'code_vs_code' | 'code_vs_doc' | 'full_analysis';
  project_id: string;
  file_id?: string;
  version_a_id?: string;
  version_b_id?: string;
  version_id?: string;
  version_id_1?: string;
  version_id_2?: string;
  filepath?: string;
  doc_version_id?: string;
}

export interface DetectConflictResponse {
  task_id: string;
  message: string;
  status: 'PROCESSING';
}

// ================================================================
// Types — Conflict Status
// ================================================================
export interface ConflictStatusResponse {
  task_id: string;
  state: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  report_id?: string;
  error?: string;
}

// ================================================================
// Types — Conflict Result
// ================================================================
export interface ConflictElement {
  type: string;
  name: string;
  class_name?: string;
}

export interface ConflictItem {
  conflict_id: string | null;
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string | null;
  element: ConflictElement;
  class_name?: string;
  member?: string;
  description: string;
  old_value: string | null;
  new_value: string | null;
  old_logic: string | null;
  new_logic: string | null;
  impact: string | null;
  suggestion: string;
  recommendation?: string;
  auto_fix_available: boolean;
  ai_confidence: number;
  doc_type?: string | null;
}

export interface DiffItem {
  diff_id: string;
  line_number: number | null;
  type: string;
  category: string;
  class_name?: string;
  member?: string;
  old_value: string;
  new_value: string;
  explanation: string;
}

export interface ClassModified {
  class_name: string;
  methods_added: string[];
  methods_removed: string[];
  methods_modified: string[];
}

export interface SuggestionItem {
  suggestion_id: string;
  priority: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  affected_files: string[];
  estimated_effort: string;
  auto_fix_available: boolean;
}

export interface MigrationStep {
  step: number;
  action: string;
  old_value: string;
  new_value: string;
  breaking: boolean;
}

export interface UndocumentedElement {
  type: string;
  name: string;
  class_name: string;
  priority: string;
  suggestion: string;
}

export interface ConflictResult {
  status: string;
  message: string;
  analysis_id: string;
  analysis_type: string;
  completed_at: string;
  execution_time_seconds: number;
  task_id: string;
  metadata: {
    project: { project_id: string; project_name: string };
    file: { file_id: string; file_name: string; file_path: string };
    versions: {
      version_a?: { version_id: string; version_number: string; role: string };
      version_b?: { version_id: string; version_number: string; role: string };
    } | null;
    documentation?: {
      doc_id: string;
      doc_version_id: string;
      file_name: string;
      type: string;
      linked_to_version: string;
      auto_fetched: boolean;
    } | null;
    code?: {
      file_id: string;
      file_name: string;
      version_id: string;
      version_number: string;
    } | null;
  };
  summary: {
    similarity_percentage: number;
    total_changes: number;
    total_conflicts: number;
    breaking_changes: number;
    grade: string;
    stats: {
      lines_added: number;
      lines_deleted: number;
      lines_modified: number;
      classes_added: number;
      classes_removed: number;
      methods_added: number;
      methods_removed: number;
      methods_modified: number;
    };
    compatibility_score?: number;
    coverage_percentage?: number;
    total_elements_analyzed?: number;
    fully_documented?: number;
    partially_documented?: number;
    undocumented?: number;
    critical_conflicts?: number;
  };
  conflicts: {
    structural: ConflictItem[];
    semantic: ConflictItem[];
    documentation: ConflictItem[];
  };
  changes: {
    diffs: DiffItem[];
    class_diagram_changes: {
      classes_added: (string | { class_name: string })[];
      classes_removed: (string | { class_name: string })[];
      classes_modified: ClassModified[];
      relationships_changed: unknown[];
    };
  };
  suggestions: SuggestionItem[];
  visual_representation?: {
    mermaid_code: string;
    svg_url: string;
  };
  summary_text: string;
  compatibility_score?: number | null;
  undocumented_elements?: UndocumentedElement[];
  migration_guide?: {
    available: boolean;
    from_version: string;
    to_version: string;
    steps: MigrationStep[];
  };
  cross_reference_analysis?: {
    changes_affecting_documentation: unknown[];
    undocumented_new_features: unknown[];
  };
  export_formats?: string[];
}

// ================================================================
// API Calls
// ================================================================

/** GET /api/upm/projects/ */
export async function fetchProjects(): Promise<UpmProject[]> {
  const res = await apiClient.get<{ results: UpmProject[] } | UpmProject[]>(
    upm('projects/')
  );
  const data = res.data;
  if (Array.isArray(data)) return data;
  if ('results' in data) return data.results;
  return [];
}

/** GET /api/upm/projects/{project_id}/tree/ — يرجع ملفات المشروع المحدد فقط */
export async function fetchProjectFiles(projectId: string): Promise<ProjectFile[]> {
  const res = await apiClient.get<{
    project_id?: string;
    project_name?: string;
    version_number?: number;
    flat_files?: Array<{
      file_id: string;
      filename: string;
      filepath: string;
      file_type?: string;
      has_documentation?: boolean;
    }>;
  }>(upm(`projects/${projectId}/tree/`));

  const data = res.data;
  
  // استخرج الملفات من الـ flat_files
  if (data.flat_files && Array.isArray(data.flat_files)) {
    return data.flat_files.map(f => ({
      file_id: f.file_id,
      filename: f.filename,
      filepath: f.filepath,
      versions_count: 1,
      has_documentation: f.has_documentation ?? false,
    }));
  }
  
  return [];
}

/** GET /api/analysis/file-versions/{file_id}/ */
export async function fetchFileVersions(fileId: string): Promise<FileVersionsResponse> {
  const res = await apiClient.get<FileVersionsResponse>(
    ai(`file-versions/${fileId}/`)
  );
  return res.data;
}

/** GET /api/analysis/file-docs/{file_id}/ */
export async function fetchFileDocs(fileId: string): Promise<FileDocsResponse> {
  const res = await apiClient.get<FileDocsResponse>(
    ai(`file-docs/${fileId}/`)
  );
  return res.data;
}

/** POST /api/analysis/upload-folder/ */
export async function uploadFolderVersion(
  zipFile: File,
  projectId: string,
  projectName: string
): Promise<UploadFolderVersion> {
  const formData = new FormData();
  formData.append('file', zipFile);
  formData.append('upm_project_id', projectId);
  formData.append('project_name', projectName);

  const res = await apiClient.post<UploadFolderVersion[]>(
    ai('upload-folder/'),
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );

  const arr = Array.isArray(res.data) ? res.data : [res.data];
  if (!arr.length) throw new Error('Upload response is empty');
  return arr[0];
}

/** POST /api/analysis/detect-conflict/ */
export async function detectConflict(
  payload: DetectConflictPayload
): Promise<DetectConflictResponse> {
  const res = await apiClient.post<DetectConflictResponse>(
    ai('detect-conflict/'),
    payload
  );
  return res.data;
}

/** GET /api/analysis/conflict-status/?task_id={id} */
export async function fetchConflictStatus(
  taskId: string
): Promise<ConflictStatusResponse> {
  const res = await apiClient.get<ConflictStatusResponse>(
    ai(`conflict-status/?task_id=${taskId}`)
  );
  return res.data;
}

/** GET /api/analysis/conflict-result/{reportId}/ */
export async function fetchConflictResult(
  reportId: string
): Promise<ConflictResult> {
  const res = await apiClient.get<ConflictResult>(
    ai(`conflict-result/${reportId}/`)
  );
  return res.data;
}

/** Polling helper — returns report_id on success */
export async function pollConflictStatus(
  taskId: string,
  options: {
    intervalMs?: number;
    maxAttempts?: number;
    onProgress?: (state: string, attempt: number) => void;
  } = {}
): Promise<string> {
  const { intervalMs = 3000, maxAttempts = 40, onProgress } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const status = await fetchConflictStatus(taskId);
    onProgress?.(status.state, attempt);

    if (status.state === 'SUCCESS' && status.report_id) {
      return status.report_id;
    }
    if (status.state === 'FAILURE') {
      throw new Error(status.error ?? 'Analysis failed');
    }

    await new Promise<void>(res => setTimeout(res, intervalMs));
  }

  throw new Error('Analysis timed out after max polling attempts');
}
