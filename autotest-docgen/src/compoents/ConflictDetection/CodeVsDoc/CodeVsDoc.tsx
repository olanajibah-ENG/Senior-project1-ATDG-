/**
 * CodeVsDoc.tsx — Real API Integration
 * Steps: project → file → versions+docs → analyze → result
 *
 * APIs:
 *   GET  /api/upm/projects/
 *   GET  /api/analysis/codefiles/?project_id=
 *   GET  /api/analysis/file-versions/{file_id}/
 *   GET  /api/analysis/file-docs/{file_id}/
 *   POST /api/analysis/detect-conflict/   (analysis_type: "code_vs_doc")
 *   GET  /api/analysis/conflict-status/?task_id=
 *   GET  /api/analysis/conflict-result/{id}/
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  X, FileText, ChevronRight, Code2, BookOpen,
  Folder, FolderOpen, CheckCircle2, ArrowRight,
  Loader2, AlertCircle, RefreshCw, GitCompare,
} from 'lucide-react';
import '../shared/conflict.theme.css';
import './CodeVsDoc.css';
import './CodeVsDoc-Enterprise.css';
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
type ResultTab = 'summary' | 'coverage' | 'ai';

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
      <div className="cvd-ci-header">
        <h4>{item.type}{item.class_name ? ` — ${item.class_name}` : ''}{item.member ? `.${item.member}` : ''}</h4>
        <span className={`cd-badge ${sev}`}>{item.severity}</span>
      </div>
      <p>{item.description}</p>
      {(item.old_value || item.new_value) && (
        <div className="cvd-ba-row">
          {item.old_value && (
            <div className="cvd-ba-col removed-bg">
              <div className="cvd-ba-label">Before</div>
              <code>{item.old_value}</code>
            </div>
          )}
          {item.new_value && (
            <div className="cvd-ba-col added-bg">
              <div className="cvd-ba-label">After</div>
              <code>{item.new_value}</code>
            </div>
          )}
        </div>
      )}
      {(item.suggestion || item.recommendation) && (
        <p className="cvd-suggestion">💡 {item.suggestion || item.recommendation}</p>
      )}
      {item.auto_fix_available && <span className="cvd-autofix-badge">✅ Auto-fix available</span>}
    </div>
  );
}

const CodeVsDoc: React.FC<Props> = ({ isOpen, onClose }) => {
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
  const [selectedVersion, setSelectedVersion] = useState<FileVersion | null>(null);

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
      if (vList.length > 0) setSelectedVersion(vList[0]);

      const dList = docsRes.docs ?? [];
      setDocs(dList);
      if (dList.length > 0) setSelectedDoc(dList[0]);
    } catch (e: unknown) {
      // non-blocking — just clear
      setVersions([]);
      setDocs([]);
    } finally {
      setVersionsLoading(false);
      setDocsLoading(false);
    }
  }, []);

  if (!isOpen) return null;

  const handleClose = () => {
    setStep('project');
    setSelectedProject(null);
    setSelectedFile(null);
    setSelectedVersion(null);
    setSelectedDoc(null);
    setResult(null);
    setAnalyzeError(null);
    setResultTab('summary');
    onClose();
  };

  const handleSelectProject = (p: UpmProject) => {
    setSelectedProject(p);
    setSelectedFile(null);
    setSelectedVersion(null);
    setSelectedDoc(null);
  };

  const handleGoToFiles = () => {
    if (!selectedProject) return;
    loadFiles(selectedProject.id);
    setStep('file');
  };

  const handleSelectFile = (f: ProjectFile) => {
    setSelectedFile(f);
    setSelectedVersion(null);
    setSelectedDoc(null);
    loadVersionsAndDocs(f.file_id);
  };

  const handleGoToSelect = () => {
    setStep('select');
  };

  const handleStartAnalysis = async () => {
    if (!selectedProject || !selectedFile || !selectedVersion || !selectedDoc) return;
    setAnalyzeError(null);
    setStep('analyzing');
    setAnalyzeProgress(5);
    try {
      setAnalyzeStep('🚀 Initializing code vs documentation analysis...');
      setAnalyzeProgress(15);
      await new Promise(r => setTimeout(r, 400));

      setAnalyzeStep('📊 Comparing code structure with documentation...');
      setAnalyzeProgress(25);

      const { task_id } = await detectConflict({
        analysis_type: 'code_vs_doc',
        project_id: selectedProject.id,
        file_id: selectedFile.file_id,
        version_id: selectedVersion.file_id || selectedFile.file_id,
        doc_version_id: selectedDoc.doc_id,
      });
      
      setAnalyzeProgress(40);
      setAnalyzeStep('🔍 Detecting inconsistencies...');
      await new Promise(r => setTimeout(r, 300));

      setAnalyzeProgress(55);
      setAnalyzeStep('⚡ Processing analysis...');
      const reportId = await pollConflictStatus(task_id, {
        intervalMs: 2500,
        maxAttempts: 40,
        onProgress: (state, attempt) => {
          const progress = Math.min(55 + attempt * 2, 88);
          setAnalyzeProgress(progress);
          const emojis = ['🔄', '⚙️', '🎯', '💫'];
          setAnalyzeStep(`${emojis[attempt % 4]} ${state}...`);
        },
      });
      
      setAnalyzeProgress(92);
      setAnalyzeStep('✨ Generating coverage map...');
      await new Promise(r => setTimeout(r, 400));

      setAnalyzeProgress(97);
      setAnalyzeStep('📦 Fetching results...');
      const res = await fetchConflictResult(reportId);
      
      setAnalyzeProgress(100);
      setAnalyzeStep('✅ Analysis complete!');
      await new Promise(r => setTimeout(r, 500));
      
      setResult(res);
      setStep('result');
    } catch (err: unknown) {
      setAnalyzeError(err instanceof Error ? err.message : 'An error occurred');
      setStep('select');
    }
  };

  const allConflicts: ConflictItem[] = result
    ? [...result.conflicts.structural, ...result.conflicts.semantic, ...result.conflicts.documentation]
    : [];

  const stepLabels = ['Project', 'File', 'Select', 'Analyzing', 'Results'];
  const stepKeys: Step[] = ['project', 'file', 'select', 'analyzing', 'result'];
  const stepIdx = stepKeys.indexOf(step);

  return (
    <div className="cvd-overlay" onClick={handleClose}>
      <div className="cvd-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="cvd-header">
          <div className="cvd-header-left">
            <div className="cvd-header-icon"><FileText size={18} color="#5b21b6" /></div>
            <div>
              <h2 className="cvd-title">Code vs Documentation</h2>
              <div className="cvd-steps">
                {stepLabels.map((s, i) => (
                  <React.Fragment key={s}>
                    <span className={`cvd-step-pill ${step === stepKeys[i] ? 'active' : stepIdx > i ? 'done' : ''}`}>
                      {stepIdx > i ? <CheckCircle2 size={9} /> : <span className="cvd-step-num">{i + 1}</span>}
                      {s}
                    </span>
                    {i < stepLabels.length - 1 && <ChevronRight size={10} className="cvd-step-sep" />}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
          {selectedProject && (
            <div className="cvd-breadcrumb">
              <Folder size={11}/><span>{selectedProject.title}</span>
              {selectedFile && <><ChevronRight size={10}/><Code2 size={11}/><span>{selectedFile.filename}</span></>}
            </div>
          )}
          <button className="cvd-close" onClick={handleClose}><X size={16}/></button>
        </div>

        {/* ─── STEP 1: PROJECT ─── */}
        {step === 'project' && (
          <div className="cvd-body cd-animate">
            <p className="cvd-section-label">Select Project</p>
            {projectsLoading && (
              <div className="cvd-loading-row"><Loader2 size={18} className="cvd-spinner" /><span>Loading projects...</span></div>
            )}
            {projectsError && (
              <div className="cvd-error-box">
                <AlertCircle size={16} />{projectsError}
                <button className="cvd-retry-btn" onClick={loadProjects}><RefreshCw size={13} />Retry</button>
              </div>
            )}
            {!projectsLoading && !projectsError && (
              <div className="cvd-project-grid">
                {projects.length === 0 && <p className="cvd-empty-note">No projects available.</p>}
                {projects.map(p => (
                  <div
                    key={p.id}
                    className={`cvd-project-card ${selectedProject?.id === p.id ? 'selected' : ''}`}
                    onClick={() => handleSelectProject(p)}
                  >
                    <div className="cvd-proj-icon">
                      {selectedProject?.id === p.id
                        ? <FolderOpen size={22} color="#a5b4fc" />
                        : <Folder size={22} color="rgba(255,255,255,0.45)" />}
                    </div>
                    <div className="cvd-proj-info">
                      <p className="cvd-proj-name">{p.title}</p>
                      <p className="cvd-proj-desc">{p.description || '—'}</p>
                      <div className="cvd-proj-meta">
                        <span className="cvd-proj-stat">{new Date(p.updated_at).toLocaleDateString('en')}</span>
                      </div>
                    </div>
                    {selectedProject?.id === p.id && <CheckCircle2 size={18} color="#5b21b6" className="cvd-proj-check" />}
                  </div>
                ))}
              </div>
            )}
            <div className="cvd-step-footer">
              <span />
              <button className="cvd-next-btn" disabled={!selectedProject} onClick={handleGoToFiles}>
                Next — Select File <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 2: FILE ─── */}
        {step === 'file' && (
          <div className="cvd-body cd-animate">
            <div className="cvd-step-context">
              <Folder size={13} color="#8b5cf6" /><span>{selectedProject?.title}</span>
            </div>
            <p className="cvd-section-label" style={{ marginTop: 12 }}>Select Code File</p>
            {filesLoading && (
              <div className="cvd-loading-row"><Loader2 size={18} className="cvd-spinner" /><span>Loading files...</span></div>
            )}
            {filesError && (
              <div className="cvd-error-box">
                <AlertCircle size={16} />{filesError}
                <button className="cvd-retry-btn" onClick={() => selectedProject && loadFiles(selectedProject.id)}>
                  <RefreshCw size={13} />Retry
                </button>
              </div>
            )}
            {!filesLoading && !filesError && (
              <div className="cvd-file-list">
                {files.length === 0 && <p className="cvd-empty-note">No files found for this project.</p>}
                {files.map(f => (
                  <div
                    key={f.file_id}
                    className={`cvd-file-row ${selectedFile?.file_id === f.file_id ? 'selected' : ''}`}
                    onClick={() => handleSelectFile(f)}
                  >
                    <div className="cvd-file-icon"><Code2 size={13} color="#8b5cf6" /></div>
                    <div className="cvd-file-info">
                      <span className="cvd-fname">{f.filename}</span>
                      <span className="cvd-fpath">{f.filepath}</span>
                    </div>
                    <span className={`cd-badge ${f.has_documentation ? 'success' : 'high'}`}>
                      {f.has_documentation ? 'Documented' : 'Not Documented'}
                    </span>
                    {selectedFile?.file_id === f.file_id && <CheckCircle2 size={15} color="#5b21b6" />}
                  </div>
                ))}
              </div>
            )}
            <div className="cvd-step-footer">
              <button className="cvd-back-btn" onClick={() => setStep('project')}>← Back</button>
              <button className="cvd-next-btn" disabled={!selectedFile} onClick={handleGoToSelect}>
                Next — Select Version & Doc <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 3: SELECT VERSION + DOC ─── */}
        {step === 'select' && (
          <div className="cvd-body cd-animate">
            <div className="cvd-step-context">
              <Folder size={13} color="#8b5cf6" /><span>{selectedProject?.title}</span>
              <ChevronRight size={11} />
              <Code2 size={13} color="#8b5cf6" /><span>{selectedFile?.filename}</span>
            </div>

            {analyzeError && (
              <div className="cvd-error-box" style={{ marginTop: 12 }}>
                <AlertCircle size={16} />{analyzeError}
              </div>
            )}

            <div className="cvd-two-col" style={{ marginTop: 14 }}>
              {/* Code version panel */}
              <div className="cvd-panel">
                <div className="cvd-panel-header">
                  <div className="cvd-panel-icon code-icon"><Code2 size={15} color="#8b5cf6" /></div>
                  <span>Code Version</span>
                </div>
                {versionsLoading ? (
                  <div className="cvd-loading-row"><Loader2 size={14} className="cvd-spinner" /><span>Loading versions...</span></div>
                ) : versions.length === 0 ? (
                  <p className="cvd-empty-note">No versions found for this file.</p>
                ) : (
                  <div className="cvd-ver-list">
                    {versions.map(v => (
                      <label
                        key={v.version_id}
                        className={`cvd-ver-row ${selectedVersion?.version_id === v.version_id ? 'sel-a' : ''}`}
                        onClick={() => setSelectedVersion(v)}
                      >
                        <span className="cvd-ver-dot" style={{
                          background: v.is_latest ? '#10b981' : 'rgba(255,255,255,0.2)'
                        }} />
                        <span className="cvd-ver-num">{v.version_number}</span>
                        <span className="cvd-ver-date">{new Date(v.created_at).toLocaleDateString('en')}</span>
                        {v.status && <span className="cvd-ver-status">{v.status}</span>}
                        {selectedVersion?.version_id === v.version_id && (
                          <CheckCircle2 size={13} color="#5b21b6" style={{ marginLeft: 'auto' }} />
                        )}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Doc panel */}
              <div className="cvd-panel">
                <div className="cvd-panel-header">
                  <div className="cvd-panel-icon doc-icon"><BookOpen size={15} color="#10b981" /></div>
                  <span>Linked Documentation</span>
                </div>
                {docsLoading ? (
                  <div className="cvd-loading-row"><Loader2 size={14} className="cvd-spinner" /><span>Loading documentation...</span></div>
                ) : docs.length === 0 ? (
                  <p className="cvd-empty-note">No documentation found for this file.</p>
                ) : (
                  <>
                    <p className="cvd-auto-note">Auto-fetched based on selected file</p>
                    {docs.map(doc => (
                      <div
                        key={doc.doc_id}
                        className={`cvd-doc-row ${selectedDoc?.doc_id === doc.doc_id ? 'selected' : ''}`}
                        onClick={() => setSelectedDoc(doc)}
                      >
                        <div className="cvd-doc-icon">
                          {doc.explanation_type === 'high_level' ? 'HL' : 'LL'}
                        </div>
                        <div className="cvd-doc-info">
                          <p className="cvd-doc-name">{doc.file_name ?? 'AI Generated Documentation'}</p>
                          <p className="cvd-doc-path">
                            {doc.explanation_type}
                            {doc.linked_to_version ? ` — Linked to ${doc.linked_to_version}` : ''}
                          </p>
                        </div>
                        {doc.relevance_score !== undefined && (
                          <div className="cvd-relevance-badge" style={{
                            background: doc.relevance_score > 0.85 ? 'rgba(16,185,129,0.2)' : 'rgba(91,33,182,0.2)',
                            color: doc.relevance_score > 0.85 ? '#10b981' : '#5b21b6',
                          }}>
                            {Math.round(doc.relevance_score * 100)}%
                          </div>
                        )}
                        {selectedDoc?.doc_id === doc.doc_id && (
                          <CheckCircle2 size={14} color="#5b21b6" />
                        )}
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>

            <div className="cvd-step-footer">
              <button className="cvd-back-btn" onClick={() => setStep('file')}>← Back</button>
              <button
                className="cvd-analyze-btn"
                disabled={!selectedVersion || !selectedDoc}
                onClick={handleStartAnalysis}
              >
                <GitCompare size={14} /> Start Analysis
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 4: ANALYZING ─── */}
        {step === 'analyzing' && (
          <div className="cvd-body cvd-analyzing-body cd-animate">
            <div className="cvd-progress-center">
              <div className="cvd-analyze-spinner-wrapper">
                <div className="cvd-spinner-orbit cvd-orbit-1"></div>
                <div className="cvd-spinner-orbit cvd-orbit-2"></div>
                <div className="cvd-spinner-orbit cvd-orbit-3"></div>
                <div className="cvd-analyze-spinner">
                  <Loader2 size={32} color="#8b5cf6" className="cvd-spinner" />
                </div>
              </div>
              <h3 className="cvd-analyzing-title">Analyzing...</h3>
              <p className="cvd-analyzing-sub">{analyzeStep}</p>
              <div className="cvd-progress-wrap">
                <div className="cvd-progress-bar">
                  <div className="cvd-progress-fill" style={{ width: `${analyzeProgress}%` }}>
                    <div className="cvd-progress-shimmer"></div>
                  </div>
                </div>
                <span className="cvd-progress-lbl">{analyzeProgress}%</span>
              </div>
              <div className="cvd-analyze-steps-list">
                {['Start Analysis', 'Compare Code with Documentation', 'Semantic Analysis', 'Process Conflicts', 'Fetch Results'].map((s, i) => {
                  const done = analyzeProgress > (i + 1) * 18;
                  const active = !done && analyzeProgress > i * 18;
                  return (
                    <div key={s} className={`cvd-analyze-step ${done ? 'done' : active ? 'active' : ''}`}>
                      <span className="cvd-step-dot" />{s}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ─── STEP 5: RESULT ─── */}
        {step === 'result' && result && (
          <div className="cvd-body cd-animate">

            {/* Context bar */}
            <div className="cvd-result-context">
              <span className="cvd-ctx-item"><Folder size={12} />{result.metadata.project.project_name}</span>
              <ChevronRight size={11} />
              <span className="cvd-ctx-item"><Code2 size={12} />{result.metadata.file.file_name}</span>
              {result.metadata.code && (
                <>
                  <ChevronRight size={11} />
                  <span className="cvd-ctx-ver">{result.metadata.code.version_number}</span>
                </>
              )}
              {result.metadata.documentation && (
                <>
                  <ChevronRight size={11} />
                  <span className="cvd-ctx-doc"><BookOpen size={11} />{result.metadata.documentation.file_name}</span>
                </>
              )}
              <span style={{ marginLeft: 'auto', fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                {result.execution_time_seconds.toFixed(1)}s
              </span>
            </div>

            {/* Stats */}
            <div className="cvd-stats-row">
              <div className="cd-stat">
                <div className="val" style={{ color: '#5b21b6' }}>{result.summary.total_conflicts}</div>
                <div className="lbl">Conflicts</div>
              </div>
              <div className="cd-stat">
                <div className="val" style={{ color: '#5b21b6' }}>
                  {result.summary.coverage_percentage != null
                    ? `${result.summary.coverage_percentage.toFixed(0)}%`
                    : '—'}
                </div>
                <div className="lbl">Coverage</div>
              </div>
              <div className="cd-stat">
                <div className="val" style={{ color: '#5b21b6' }}>
                  {result.summary.compatibility_score != null
                    ? `${result.summary.compatibility_score.toFixed(0)}%`
                    : '—'}
                </div>
                <div className="lbl">Compatibility</div>
              </div>
              <div className="cd-stat">
                <div className="val" style={{ color: '#5b21b6' }}>{result.summary.grade}</div>
                <div className="lbl">Grade</div>
              </div>
            </div>

            {result.summary_text && (
              <div className="cvd-summary-text">{result.summary_text}</div>
            )}

            {/* Tabs */}
            <div className="cd-tab-bar">
              {(['summary', 'coverage', 'ai'] as ResultTab[]).map(t => (
                <button
                  key={t}
                  className={`cd-tab ${resultTab === t ? 'active' : ''}`}
                  onClick={() => setResultTab(t)}
                >
                  {t === 'summary' ? 'Conflicts' : t === 'coverage' ? 'Coverage Map' : 'AI Suggestions'}
                </button>
              ))}
            </div>

            {/* ── Tab: Summary ── */}
            {resultTab === 'summary' && (
              <div className="cd-animate">
                {allConflicts.length === 0 && (
                  <p className="cvd-empty-note">No conflicts found.</p>
                )}
                {allConflicts.map((c, i) => <ConflictCard key={i} item={c} />)}
              </div>
            )}

            {/* ── Tab: Coverage Map ── */}
            {resultTab === 'coverage' && (
              <div className="cd-animate">
                <div className="cvd-coverage-header">
                  <p className="cvd-preview-title">Coverage Map — {result.metadata.file.file_name}</p>
                  {result.summary.coverage_percentage != null && (
                    <div className="cvd-total-bar">
                      <div style={{
                        width: `${result.summary.coverage_percentage}%`,
                        background: 'linear-gradient(90deg,#8b5cf6,#10b981)'
                      }} />
                      <span>{result.summary.coverage_percentage.toFixed(0)}%</span>
                    </div>
                  )}
                </div>

                {/* Stats grid */}
                <div className="cvd-cov-stats-grid">
                  {[
                    { l: 'Elements Analyzed', v: result.summary.total_elements_analyzed ?? '—', c: '#fff' },
                    { l: 'Fully Documented', v: result.summary.fully_documented ?? '—', c: '#10b981' },
                    { l: 'Partially Documented', v: result.summary.partially_documented ?? '—', c: '#5b21b6' },
                    { l: 'Undocumented', v: result.summary.undocumented ?? '—', c: '#ef4444' },
                  ].map(s => (
                    <div key={s.l} className="cvd-cov-stat">
                      <span className="cvd-cov-val" style={{ color: s.c }}>{s.v}</span>
                      <span className="cvd-cov-lbl">{s.l}</span>
                    </div>
                  ))}
                </div>

                {/* Undocumented elements */}
                {result.undocumented_elements && result.undocumented_elements.length > 0 && (
                  <div className="cvd-undoc-list">
                    <p className="cvd-preview-title" style={{ marginBottom: 8 }}>Undocumented Elements</p>
                    {result.undocumented_elements.map((u, i) => (
                      <div key={i} className="cvd-undoc-row">
                        <span className="cvd-undoc-type">{u.type}</span>
                        <span className="cvd-undoc-name">{u.name}</span>
                        <span className="cvd-undoc-class">({u.class_name})</span>
                        <span className={`cd-badge ${SEV[u.priority] ?? 'medium'}`}>{u.priority}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Docs conflicts */}
                {result.conflicts.documentation.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <p className="cvd-preview-title" style={{ marginBottom: 8 }}>Documentation Details</p>
                    {result.conflicts.documentation.map((c, i) => <ConflictCard key={i} item={c} />)}
                  </div>
                )}
              </div>
            )}

            {/* ── Tab: AI Suggestions ── */}
            {resultTab === 'ai' && (
              <div className="cd-animate">
                {result.suggestions.length === 0 && (
                  <p className="cvd-empty-note">No suggestions available.</p>
                )}
                {result.suggestions.map(s => (
                  <div key={s.suggestion_id} className={`cd-conflict-item ${SEV[s.priority] ?? 'medium'}`}>
                    <div className="cvd-ci-header">
                      <h4>{s.title}</h4>
                      <span className={`cd-badge ${SEV[s.priority] ?? 'medium'}`}>{s.priority}</span>
                    </div>
                    <p>{s.description}</p>
                    <p className="cvd-suggestion">⏱ {s.estimated_effort}</p>
                    {s.auto_fix_available && <span className="cvd-autofix-badge">✅ Auto-fix available</span>}
                  </div>
                ))}
              </div>
            )}

            <div className="cvd-footer-bar">
              <button className="cvd-back-btn" onClick={() => { setStep('select'); setResult(null); }}>← New Analysis</button>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>ID: {result.analysis_id.slice(-8)}</span>
                <button className="cvd-export-btn">Export PDF</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default CodeVsDoc;
