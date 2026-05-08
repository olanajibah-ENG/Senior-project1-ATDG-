/**
 * FullAnalysis.tsx — Real API Integration
 * Steps: project → file → versions + doc → analyze → result
 *
 * APIs:
 *   GET  /api/upm/projects/
 *   GET  /api/analysis/codefiles/?project_id=
 *   GET  /api/analysis/file-versions/{file_id}/
 *   GET  /api/analysis/file-docs/{file_id}/
 *   POST /api/analysis/detect-conflict/   (analysis_type: "full_analysis")
 *   GET  /api/analysis/conflict-status/?task_id=
 *   GET  /api/analysis/conflict-result/{id}/
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  X, Star, ChevronRight, GitCompare, FileText, Map, ArrowRight,
  Folder, FolderOpen, Code2, BookOpen, CheckCircle2, Plus, Minus, Edit3,
  Loader2, AlertCircle, RefreshCw,
} from 'lucide-react';
import '../shared/conflict.theme.css';
import './FullAnalysis.css';
import './FullAnalysis-Enterprise.css';
import '../shared/conflict-enterprise-dark.css';
import '../shared/unified-dark-purple-theme.css';
import {
  fetchProjects,
  fetchProjectFiles,
  fetchFileVersions,
  fetchFileDocs,
  detectConflict,
  pollConflictStatus,
  fetchConflictResult,
} from '../../../services/conflictDetection.service';
import type {
  UpmProject,
  ProjectFile,
  FileVersion,
  FileDoc,
  ConflictResult,
  ConflictItem,
} from '../../../services/conflictDetection.service';

type Step = 'project' | 'file' | 'select' | 'analyzing' | 'result';
type ResultTab = 'summary' | 'code' | 'doc' | 'migration';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const SEV: Record<string, string> = {
  critical: 'critical', high: 'high', medium: 'medium', low: 'success', info: 'success',
};

function ConflictCard({ item }: { item: ConflictItem }) {
  const sev = SEV[item.severity] ?? 'medium';
  return (
    <div className={`cd-conflict-item ${sev}`}>
      <div className="fa-ci-row">
        <h4>{item.type}{item.class_name ? ` — ${item.class_name}` : ''}{item.member ? `.${item.member}` : ''}</h4>
        <span className={`cd-badge ${sev}`}>{item.severity}</span>
      </div>
      <p>{item.description}</p>
      {(item.old_value || item.new_value) && (
        <div className="fa-before-after">
          {item.old_value && (
            <div className="fa-ba removed-bg">
              <span className="fa-ba-label">Before</span>
              <code>{item.old_value}</code>
            </div>
          )}
          {item.new_value && (
            <div className="fa-ba added-bg">
              <span className="fa-ba-label">After</span>
              <code>{item.new_value}</code>
            </div>
          )}
        </div>
      )}
      {(item.suggestion || item.recommendation) && (
        <p className="fa-suggestion">💡 {item.suggestion || item.recommendation}</p>
      )}
    </div>
  );
}

const FullAnalysis: React.FC<Props> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState<Step>('project');

  /* Projects */
  const [projects, setProjects] = useState<UpmProject[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<UpmProject | null>(null);

  /* Files */
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [filesError, setFilesError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<ProjectFile | null>(null);

  /* Versions */
  const [versions, setVersions] = useState<FileVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionA, setVersionA] = useState<FileVersion | null>(null);
  const [versionB, setVersionB] = useState<FileVersion | null>(null);

  /* Docs */
  const [docs, setDocs] = useState<FileDoc[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<FileDoc | null>(null);

  /* Analysis */
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analyzeStep, setAnalyzeStep] = useState('');
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [result, setResult] = useState<ConflictResult | null>(null);
  const [resultTab, setResultTab] = useState<ResultTab>('summary');

  const loadProjects = useCallback(() => {
    setProjectsLoading(true);
    setProjectsError(null);
    fetchProjects()
      .then(setProjects)
      .catch(e => setProjectsError(e.message ?? 'Failed to load projects'))
      .finally(() => setProjectsLoading(false));
  }, []);

  useEffect(() => {
    if (isOpen) loadProjects();
  }, [isOpen, loadProjects]);

  const loadFiles = useCallback((projectId: string) => {
    setFilesLoading(true);
    setFilesError(null);
    fetchProjectFiles(projectId)
      .then(setFiles)
      .catch(e => setFilesError(e.message ?? 'Failed to load files'))
      .finally(() => setFilesLoading(false));
  }, []);

  const loadVersionsAndDocs = useCallback(async (fileId: string) => {
    setVersionsLoading(true);
    setDocsLoading(true);
    try {
      const [versionsRes, docsRes] = await Promise.all([
        fetchFileVersions(fileId),
        fetchFileDocs(fileId),
      ]);
      const vList = versionsRes.history ?? [];
      setVersions(vList);
      if (vList.length > 0) setVersionA(vList[0]);
      if (vList.length > 1) setVersionB(vList[1]);

      const dList = docsRes.docs ?? [];
      setDocs(dList);
      if (dList.length > 0) setSelectedDoc(dList[0]);
    } catch {
      setVersions([]); setDocs([]);
    } finally {
      setVersionsLoading(false);
      setDocsLoading(false);
    }
  }, []);

  if (!isOpen) return null;

  const handleClose = () => {
    setStep('project');
    setSelectedProject(null); setSelectedFile(null);
    setVersionA(null); setVersionB(null); setSelectedDoc(null);
    setResult(null); setAnalyzeError(null); setResultTab('summary');
    onClose();
  };

  const handleSelectProject = (p: UpmProject) => {
    setSelectedProject(p);
    setSelectedFile(null); setVersionA(null); setVersionB(null); setSelectedDoc(null);
  };

  const handleGoToFiles = () => {
    if (!selectedProject) return;
    loadFiles(selectedProject.id);
    setStep('file');
  };

  const handleSelectFile = (f: ProjectFile) => {
    setSelectedFile(f);
    setVersionA(null); setVersionB(null); setSelectedDoc(null);
    loadVersionsAndDocs(f.file_id);
  };

  const handleStartAnalysis = async () => {
    if (!selectedProject || !selectedFile || !versionA || !versionB) return;
    setAnalyzeError(null);
    setStep('analyzing');
    setAnalyzeProgress(5);
    try {
      setAnalyzeStep('🚀 Starting comprehensive analysis...');
      setAnalyzeProgress(20);

      const payload: Parameters<typeof detectConflict>[0] = {
        analysis_type: 'full_analysis',
        project_id: selectedProject.id,
        file_id: selectedFile.file_id,
        version_id_1: versionA.version_id,
        version_id_2: versionB.version_id,
      };
      if (selectedDoc) payload.doc_version_id = selectedDoc.doc_id;

      const { task_id } = await detectConflict(payload);
      setAnalyzeProgress(35);

      setAnalyzeStep('⚡ Processing full analysis...');
      const reportId = await pollConflictStatus(task_id, {
        intervalMs: 3000, maxAttempts: 60,
        onProgress: (state, attempt) => {
          setAnalyzeProgress(Math.min(35 + attempt * 1.5, 92));
          const emojis = ['🔄', '⚙️', '🎯', '💫'];
          setAnalyzeStep(`${emojis[attempt % 4]} ${state}...`);
        },
      });
      setAnalyzeProgress(96);

      setAnalyzeStep('📦 Fetching results...');
      const res = await fetchConflictResult(reportId);
      setResult(res);
      setAnalyzeProgress(100);
      setStep('result');
    } catch (err: unknown) {
      setAnalyzeError(err instanceof Error ? err.message : 'An error occurred');
      setStep('select');
    }
  };

  const allConflicts: ConflictItem[] = result
    ? [...result.conflicts.structural, ...result.conflicts.semantic, ...result.conflicts.documentation]
    : [];
  const codeConflicts: ConflictItem[] = result
    ? [...result.conflicts.structural, ...result.conflicts.semantic]
    : [];
  const docConflicts: ConflictItem[] = result
    ? result.conflicts.documentation
    : [];

  const stepLabels = ['Project', 'File', 'Select', 'Analyzing', 'Results'];
  const stepKeys: Step[] = ['project', 'file', 'select', 'analyzing', 'result'];
  const stepIdx = stepKeys.indexOf(step);

  return (
    <div className="fa-overlay" onClick={handleClose}>
      <div className="fa-modal" onClick={e => e.stopPropagation()}>

        {/* ===== Header ===== */}
        <div className="fa-header">
          <div className="fa-header-left">
            <div className="fa-header-icon"><Star size={18} color="#5b21b6" /></div>
            <div>
              <h2 className="fa-title">Full Analysis</h2>
              <div className="fa-steps">
                {stepLabels.map((s, i) => (
                  <React.Fragment key={s}>
                    <span className={`fa-step-pill ${step === stepKeys[i] ? 'active' : stepIdx > i ? 'done' : ''}`}>
                      {stepIdx > i ? <CheckCircle2 size={9} /> : <span className="fa-step-num">{i + 1}</span>}
                      {s}
                    </span>
                    {i < stepLabels.length - 1 && <ChevronRight size={10} className="fa-step-sep" />}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
          {selectedProject && (
            <div className="fa-breadcrumb">
              <Folder size={11}/><span>{selectedProject.title}</span>
              {selectedFile && <><ChevronRight size={10}/><Code2 size={11}/><span>{selectedFile.filename}</span></>}
            </div>
          )}
          <button className="fa-close" onClick={handleClose}><X size={16}/></button>
        </div>

        {/* ===== STEP 1: PROJECT ===== */}
        {step === 'project' && (
          <div className="fa-body cd-animate">
            <p className="fa-section-label">Select Project</p>
            {projectsLoading && (
              <div className="fa-loading-row"><Loader2 size={18} className="fa-spinner" /><span>Loading projects...</span></div>
            )}
            {projectsError && (
              <div className="fa-error-box">
                <AlertCircle size={16} />{projectsError}
                <button className="fa-retry-btn" onClick={loadProjects}><RefreshCw size={13} />Retry</button>
              </div>
            )}
            {!projectsLoading && !projectsError && (
              <div className="fa-project-grid">
                {projects.length === 0 && <p className="fa-empty-note">No projects available.</p>}
                {projects.map(p => (
                  <div
                    key={p.id}
                    className={`fa-project-card ${selectedProject?.id === p.id ? 'selected' : ''}`}
                    onClick={() => handleSelectProject(p)}
                  >
                    <div className="fa-proj-icon">
                      {selectedProject?.id === p.id
                        ? <FolderOpen size={22} color="#a5b4fc" />
                        : <Folder size={22} color="rgba(255,255,255,0.45)" />}
                    </div>
                    <div className="fa-proj-info">
                      <p className="fa-proj-name">{p.title}</p>
                      <p className="fa-proj-desc">{p.description || '—'}</p>
                      <div className="fa-proj-meta">
                        <span className="fa-proj-stat">{new Date(p.updated_at).toLocaleDateString('en')}</span>
                      </div>
                    </div>
                    {selectedProject?.id === p.id && <CheckCircle2 size={18} color="#5b21b6" className="fa-proj-check" />}
                  </div>
                ))}
              </div>
            )}
            <div className="fa-step-footer">
              <span />
              <button className="fa-next-btn" disabled={!selectedProject} onClick={handleGoToFiles}>
                Next — Select File <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ===== STEP 2: FILE ===== */}
        {step === 'file' && (
          <div className="fa-body cd-animate">
            <div className="fa-step-context">
              <Folder size={13} color="#a855f7" /><span>{selectedProject?.title}</span>
            </div>
            <p className="fa-section-label" style={{ marginTop: 12 }}>Select Code File</p>
            {filesLoading && (
              <div className="fa-loading-row"><Loader2 size={18} className="fa-spinner" /><span>Loading files...</span></div>
            )}
            {filesError && (
              <div className="fa-error-box">
                <AlertCircle size={16} />{filesError}
                <button className="fa-retry-btn" onClick={() => selectedProject && loadFiles(selectedProject.id)}>
                  <RefreshCw size={13} />Retry
                </button>
              </div>
            )}
            {!filesLoading && !filesError && (
              <div className="fa-file-list">
                {files.length === 0 && <p className="fa-empty-note">No files found for this project.</p>}
                {files.map(f => (
                  <div
                    key={f.file_id}
                    className={`fa-file-row ${selectedFile?.file_id === f.file_id ? 'selected' : ''}`}
                    onClick={() => handleSelectFile(f)}
                  >
                    <div className="fa-file-icon"><GitCompare size={13} color="#a855f7" /></div>
                    <div className="fa-file-info">
                      <span className="fa-fname">{f.filename}</span>
                      <span className="fa-fpath">{f.filepath}</span>
                    </div>
                    <span className={`cd-badge ${f.has_documentation ? 'success' : 'high'}`}>
                      {f.has_documentation ? 'Documented' : 'Not Documented'}
                    </span>
                    {selectedFile?.file_id === f.file_id && <CheckCircle2 size={15} color="#5b21b6" />}
                  </div>
                ))}
              </div>
            )}
            <div className="fa-step-footer">
              <button className="fa-back-btn" onClick={() => setStep('project')}>← Back</button>
              <button className="fa-next-btn" disabled={!selectedFile} onClick={() => setStep('select')}>
                Next — Select Versions & Doc <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ===== STEP 3: SELECT VERSIONS + DOC ===== */}
        {step === 'select' && (
          <div className="fa-body cd-animate">
            <div className="fa-step-context">
              <Folder size={13} color="#a855f7" /><span>{selectedProject?.title}</span>
              <ChevronRight size={11} />
              <Code2 size={13} color="#a855f7" /><span>{selectedFile?.filename}</span>
            </div>

            {analyzeError && (
              <div className="fa-error-box" style={{ marginTop: 12 }}>
                <AlertCircle size={16} />{analyzeError}
              </div>
            )}

            <div className="fa-select-grid" style={{ marginTop: 14 }}>
              {/* Versions */}
              <div className="fa-section">
                <p className="fa-section-label">Versions</p>
                {versionsLoading ? (
                  <div className="fa-loading-row"><Loader2 size={14} className="fa-spinner" /><span>Loading versions...</span></div>
                ) : versions.length === 0 ? (
                  <p className="fa-empty-note">No versions found for this file.</p>
                ) : (
                  <div className="fa-versions-grid">
                    {/* Version A */}
                    <div>
                      <p className="fa-ver-sublabel ver-a-color">Version A — Reference</p>
                      {versions.map(v => (
                        <label
                          key={v.version_id}
                          className={`fa-ver-row ${versionA?.version_id === v.version_id ? 'sel-a' : ''}`}
                          onClick={() => setVersionA(v)}
                        >
                          <span className="fa-ver-dot" style={{ background: v.is_latest ? '#10b981' : 'rgba(255,255,255,0.2)' }} />
                          <span className="fa-ver-num">{v.version_number}</span>
                          <span className="fa-ver-date">{new Date(v.created_at).toLocaleDateString('ar')}</span>
                          {versionA?.version_id === v.version_id && (
                            <CheckCircle2 size={13} color="#5b21b6" style={{ marginLeft: 'auto' }} />
                          )}
                        </label>
                      ))}
                    </div>
                    <div className="fa-arrow-col"><ArrowRight size={16} color="rgba(255,255,255,0.3)" /></div>
                    {/* Version B */}
                    <div>
                      <p className="fa-ver-sublabel ver-b-color">Version B — New</p>
                      {versions.map(v => (
                        <label
                          key={v.version_id}
                          className={`fa-ver-row ${versionB?.version_id === v.version_id ? 'sel-b' : ''}`}
                          onClick={() => setVersionB(v)}
                        >
                          <span className="fa-ver-dot" style={{ background: v.is_latest ? '#10b981' : 'rgba(255,255,255,0.2)' }} />
                          <span className="fa-ver-num">{v.version_number}</span>
                          <span className="fa-ver-date">{new Date(v.created_at).toLocaleDateString('ar')}</span>
                          {versionB?.version_id === v.version_id && (
                            <CheckCircle2 size={13} color="#5b21b6" style={{ marginLeft: 'auto' }} />
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Doc auto-fetch */}
              <div className="fa-section fa-doc-section">
                <p className="fa-section-label">Documentation</p>
                {docsLoading ? (
                  <div className="fa-loading-row"><Loader2 size={14} className="fa-spinner" /><span>Loading documentation...</span></div>
                ) : docs.length === 0 ? (
                  <div className="fa-doc-auto">
                    <div className="fa-doc-auto-icon"><FileText size={14} color="rgba(255,255,255,0.3)" /></div>
                    <div>
                      <p className="fa-doc-auto-title">No Documentation</p>
                      <p className="fa-doc-auto-sub">Analysis will include code vs code only</p>
                    </div>
                    <span className="cd-badge medium">Optional</span>
                  </div>
                ) : (
                  <div>
                    <p className="fa-auto-note">Auto-fetched based on file</p>
                    {docs.map(doc => (
                      <div
                        key={doc.doc_id}
                        className={`fa-doc-row ${selectedDoc?.doc_id === doc.doc_id ? 'selected' : ''}`}
                        onClick={() => setSelectedDoc(doc)}
                      >
                        <div className="fa-doc-auto-icon"><FileText size={14} color="#5b21b6" /></div>
                        <div>
                          <p className="fa-doc-auto-title">{doc.file_name ?? 'AI Generated Documentation'}</p>
                          <p className="fa-doc-auto-sub">
                            {doc.explanation_type}
                            {doc.linked_to_version ? ` — Linked to ${doc.linked_to_version}` : ''}
                          </p>
                        </div>
                        <span className="cd-badge success">
                          {selectedDoc?.doc_id === doc.doc_id ? '✓ Selected' : 'Ready'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              className="fa-start-btn"
              disabled={!versionA || !versionB || versionA.version_id === versionB.version_id}
              onClick={handleStartAnalysis}
            >
              <Star size={15} /> Start Full Analysis
            </button>

            <div className="fa-step-footer" style={{ borderTop: 'none', paddingTop: 8 }}>
              <button className="fa-back-btn" onClick={() => setStep('file')}>← Back</button>
            </div>
          </div>
        )}

        {/* ===== STEP 4: ANALYZING ===== */}
        {step === 'analyzing' && (
          <div className="fa-body fa-analyzing cd-animate">
            <div className="fa-analysis-center">
              <div className="fa-spinner-wrap">
                <Star size={28} color="#a855f7" className="fa-spin-icon" />
              </div>
              <h3 className="fa-analyzing-title">Running Full Analysis...</h3>
              <p className="fa-analyzing-sub">{analyzeStep}</p>
              <div className="fa-progress-wrap">
                <div className="fa-progress-bar">
                  <div className="fa-progress-fill" style={{ width: `${analyzeProgress}%` }} />
                </div>
                <span className="fa-progress-pct">{analyzeProgress}%</span>
              </div>
              <div className="fa-steps-list">
                {['Code vs Code Analysis', 'Class Diagram Comparison', 'Code vs Documentation', 'Migration Guide Generation'].map((s, i) => {
                  const done = analyzeProgress > (i + 1) * 22;
                  const active = !done && analyzeProgress > i * 22;
                  return (
                    <div key={s} className={`fa-step-item ${done ? 'done' : active ? 'active' : ''}`}>
                      <span className="fa-step-dot" />{s}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ===== STEP 5: RESULT ===== */}
        {step === 'result' && result && (
          <div className="fa-body cd-animate">

            {/* Context */}
            <div className="fa-result-context">
              <span className="fa-ctx-item"><Folder size={12} />{result.metadata.project.project_name}</span>
              <ChevronRight size={11} />
              <span className="fa-ctx-item"><Code2 size={12} />{result.metadata.file.file_name}</span>
              {result.metadata.versions?.version_a && (
                <>
                  <ChevronRight size={11} />
                  <span className="fa-ctx-ver ver-a-text">{result.metadata.versions.version_a.version_number}</span>
                  <ArrowRight size={11} />
                  <span className="fa-ctx-ver ver-b-text">{result.metadata.versions.version_b?.version_number}</span>
                </>
              )}
              <span style={{ marginLeft: 'auto', fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                {result.execution_time_seconds.toFixed(1)}s
              </span>
            </div>

            {/* Grade + stats */}
            <div className="fa-result-top">
              <div className="fa-grade-block">
                <div className={`fa-grade-circle grade-${result.summary.grade}`}>{result.summary.grade}</div>
                <div>
                  <p className="fa-grade-label">Overall Grade</p>
                  <p className="fa-grade-sub">
                    {result.summary.compatibility_score != null && `Compatibility: ${result.summary.compatibility_score.toFixed(0)}%`}
                    {result.summary.similarity_percentage > 0 && ` — Similarity: ${result.summary.similarity_percentage}%`}
                  </p>
                </div>
              </div>
              <div className="fa-stats-row">
                <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary.total_conflicts}</div><div className="lbl">Total</div></div>
                <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary.critical_conflicts ?? 0}</div><div className="lbl">critical</div></div>
                <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary.breaking_changes}</div><div className="lbl">breaking</div></div>
                <div className="cd-stat">
                  <div className="val" style={{ color: '#5b21b6' }}>
                    {result.summary.coverage_percentage != null
                      ? `${result.summary.coverage_percentage.toFixed(0)}%`
                      : '—'}
                  </div>
                  <div className="lbl">doc coverage</div>
                </div>
              </div>
            </div>

            {result.summary_text && (
              <div className="fa-summary-text">{result.summary_text}</div>
            )}

            {/* Legend */}
            <div className="cd-legend">
              <span><span className="cd-legend-dot" style={{ background: '#10b981' }} />Added</span>
              <span><span className="cd-legend-dot" style={{ background: '#ef4444' }} />Removed</span>
              <span><span className="cd-legend-dot" style={{ background: '#f59e0b' }} />Modified</span>
            </div>

            {/* Tabs */}
            <div className="cd-tab-bar">
              {(['summary', 'code', 'doc', 'migration'] as ResultTab[]).map(t => (
                <button
                  key={t}
                  className={`cd-tab ${resultTab === t ? 'active' : ''}`}
                  onClick={() => setResultTab(t)}
                >
                  {t === 'summary' ? 'Full Summary' : t === 'code' ? 'Code Conflicts' : t === 'doc' ? 'Doc Conflicts' : 'Migration Guide'}
                </button>
              ))}
            </div>

            {/* ── Summary ── */}
            {resultTab === 'summary' && (
              <div className="fa-summary cd-animate">
                <div className="fa-summary-grid">
                  <div>
                    <p className="fa-col-title"><GitCompare size={13} /> Code Conflicts</p>
                    {codeConflicts.length === 0
                      ? <p className="fa-empty-note">No code conflicts found.</p>
                      : codeConflicts.map((c, i) => <ConflictCard key={i} item={c} />)}
                  </div>
                  <div>
                    <p className="fa-col-title"><FileText size={13} /> Documentation Conflicts</p>
                    {docConflicts.length === 0
                      ? <p className="fa-empty-note">No documentation conflicts found.</p>
                      : docConflicts.map((c, i) => <ConflictCard key={i} item={c} />)}
                  </div>
                </div>

                {/* Cross reference */}
                {result.cross_reference_analysis && (
                  result.cross_reference_analysis.changes_affecting_documentation.length > 0 ||
                  result.cross_reference_analysis.undocumented_new_features.length > 0
                ) && (
                  <div className="fa-cross-ref">
                    <div className="fa-cross-icon">⚡</div>
                    <div>
                      <p className="fa-cross-title">Cross Reference — Impact Analysis</p>
                      <p className="fa-cross-desc">
                        {result.cross_reference_analysis.undocumented_new_features.length} undocumented new features
                        {' '}and{' '}
                        {result.cross_reference_analysis.changes_affecting_documentation.length} changes affecting documentation.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Code Conflicts ── */}
            {resultTab === 'code' && (
              <div className="cd-animate">
                {codeConflicts.length === 0
                  ? <p className="fa-empty-note">No code conflicts found.</p>
                  : codeConflicts.map((c, i) => <ConflictCard key={i} item={c} />)}

                {/* Class diagram changes */}
                {result.changes.class_diagram_changes.classes_modified.length > 0 && (
                  <div className="fa-uml-section">
                    <p className="fa-col-title" style={{ marginBottom: 10 }}>Class Diagram Changes</p>
                    <div className="fa-uml-grid">
                      {result.changes.class_diagram_changes.classes_modified.map(cls => (
                        <div key={cls.class_name} className="fa-uml-node">
                          <div className="fa-uml-header">{cls.class_name}</div>
                          <div className="fa-uml-body">
                            {cls.methods_added.map(m => (
                              <div key={m} className="fa-uml-member added"><Plus size={10} />{m}</div>
                            ))}
                            {cls.methods_modified.map(m => (
                              <div key={m} className="fa-uml-member modified"><Edit3 size={10} />{m}</div>
                            ))}
                            {cls.methods_removed.map(m => (
                              <div key={m} className="fa-uml-member removed"><Minus size={10} />{m}</div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="fa-uml-summary">
                      <span className="fa-uml-sum added"><Plus size={11} />{result.summary.stats.methods_added} added</span>
                      <span className="fa-uml-sum removed"><Minus size={11} />{result.summary.stats.methods_removed} removed</span>
                      <span className="fa-uml-sum modified"><Edit3 size={11} />{result.summary.stats.methods_modified} modified</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Doc Conflicts ── */}
            {resultTab === 'doc' && (
              <div className="cd-animate">
                {docConflicts.length === 0
                  ? <p className="fa-empty-note">No documentation conflicts found.</p>
                  : docConflicts.map((c, i) => <ConflictCard key={i} item={c} />)}

                {result.undocumented_elements && result.undocumented_elements.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <p className="fa-col-title" style={{ marginBottom: 8 }}>Undocumented Elements</p>
                    {result.undocumented_elements.map((u, i) => (
                      <div key={i} className="fa-undoc-row">
                        <span className="fa-undoc-type">{u.type}</span>
                        <span className="fa-undoc-name">{u.name}</span>
                        <span className="fa-undoc-class">({u.class_name})</span>
                        <span className={`cd-badge ${SEV[u.priority] ?? 'medium'}`}>{u.priority}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── Migration Guide ── */}
            {resultTab === 'migration' && (
              <div className="fa-migration cd-animate">
                <div className="fa-migration-header">
                  <Map size={14} color="#a855f7" />
                  <span>
                    Migration Guide
                    {result.migration_guide
                      ? ` — ${result.migration_guide.from_version} → ${result.migration_guide.to_version}`
                      : ''}
                  </span>
                </div>

                {(!result.migration_guide || !result.migration_guide.available) ? (
                  <p className="fa-empty-note">No migration guide available for this analysis.</p>
                ) : (
                  result.migration_guide.steps.map(m => (
                    <div key={m.step} className="fa-migration-step">
                      <div className="fa-step-num-circle" style={{ background: m.breaking ? '#ef4444' : '#8b5cf6' }}>
                        {m.step}
                      </div>
                      <div className="fa-step-body">
                        <div className="fa-step-title">
                          <span>{m.action}</span>
                          {m.breaking && <span className="fa-breaking-tag">Breaking</span>}
                        </div>
                        <div className="fa-step-code-pair">
                          {m.old_value && (
                            <div className="fa-step-code removed-bg">
                              <span className="fa-step-code-label">Before</span>
                              <pre>{m.old_value}</pre>
                            </div>
                          )}
                          {m.new_value && (
                            <div className="fa-step-code added-bg">
                              <span className="fa-step-code-label">After</span>
                              <pre>{m.new_value}</pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}

                {result.suggestions.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <p className="fa-col-title" style={{ marginBottom: 8 }}>Additional Suggestions</p>
                    {result.suggestions.slice(0, 5).map(s => (
                      <div key={s.suggestion_id} className={`cd-conflict-item ${SEV[s.priority] ?? 'medium'}`} style={{ marginBottom: 8 }}>
                        <div className="fa-ci-row">
                          <h4>{s.title}</h4>
                          <span className={`cd-badge ${SEV[s.priority] ?? 'medium'}`}>{s.priority}</span>
                        </div>
                        <p>{s.description}</p>
                        <p className="fa-suggestion">⏱ {s.estimated_effort}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="fa-result-footer">
              <button className="fa-back-btn" onClick={() => { setStep('select'); setResult(null); }}>← New Analysis</button>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>ID: {result.analysis_id.slice(-8)}</span>
                <button className="fa-export-btn">Export PDF</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default FullAnalysis;
