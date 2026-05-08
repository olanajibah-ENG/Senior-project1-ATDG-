/**
 * CodeVsCode.tsx — Redesigned with streamlined flow:
 * Step 1: Select Project
 * Step 2: Pick file from project
 * Step 3: Select 2 versions side-by-side
 * Step 4: Analyzing
 * Step 5: Result (Code Diff / Class Diagram Diff / AI)
 */

import React, { useState, useEffect } from 'react';
import {
  X, GitCompare, ChevronRight, ArrowRight,
  Code2, GitBranch, Folder, FolderOpen,
  CheckCircle2, Plus, Minus, Edit3,
  Loader2, AlertCircle, RefreshCw,
  FileCode, Star
} from 'lucide-react';
import '../shared/conflict.theme.css';
import './CodeVsCode.css';
import './CodeVsCode-Enterprise.css';
import '../shared/conflict-enterprise-dark.css';
import '../shared/unified-dark-purple-theme.css';
import {
  fetchProjects,
  fetchProjectFiles,
  fetchFileVersions,
  detectConflict,
  pollConflictStatus,
  fetchConflictResult,
} from '../../../services/conflictDetection.service';
import type {
  UpmProject,
  ProjectFile,
  FileVersion,
  ConflictResult,
  ConflictItem,
} from '../../../services/conflictDetection.service';

type Step = 'project' | 'file-pick' | 'version-pick' | 'analyzing' | 'result';
type ResultTab = 'summary' | 'diff' | 'diagram' | 'ai';

interface Props { isOpen: boolean; onClose: () => void; }

const SEV: Record<string, string> = {
  critical: 'critical', high: 'high', medium: 'medium', low: 'success',
};

function GradeCircle({ grade }: { grade: string }) {
  const cls = grade === 'A' ? 'A' : grade === 'B' ? 'B' : 'C';
  return <div className={`cd-grade ${cls}`}>{grade}</div>;
}

/* ─── Enhanced Side-by-Side Diff with Animations ─── */
interface DiffLineData {
  lineNumA: number | null;
  lineNumB: number | null;
  type: 'added' | 'removed' | 'unchanged' | 'modified';
  content: string;
  highlight?: boolean;
}

function buildSideBySideDiff(linesA: string[], linesB: string[]): { left: DiffLineData[]; right: DiffLineData[] } {
  // Enhanced LCS-based diff with modification detection
  const m = linesA.length, n = linesB.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--)
    for (let j = n - 1; j >= 0; j--)
      dp[i][j] = linesA[i] === linesB[j] ? dp[i+1][j+1] + 1 : Math.max(dp[i+1][j], dp[i][j+1]);

  const left: DiffLineData[] = [], right: DiffLineData[] = [];
  let i = 0, j = 0, la = 1, lb = 1;
  
  while (i < m || j < n) {
    if (i < m && j < n && linesA[i] === linesB[j]) {
      left.push({ lineNumA: la++, lineNumB: null, type: 'unchanged', content: linesA[i] });
      right.push({ lineNumA: null, lineNumB: lb++, type: 'unchanged', content: linesB[j] });
      i++; j++;
    } else if (i < m && j < n && linesA[i].trim() && linesB[j].trim() && 
               linesA[i].substring(0, 10) === linesB[j].substring(0, 10)) {
      // Detect modifications (similar lines)
      left.push({ lineNumA: la++, lineNumB: null, type: 'modified', content: linesA[i], highlight: true });
      right.push({ lineNumA: null, lineNumB: lb++, type: 'modified', content: linesB[j], highlight: true });
      i++; j++;
    } else if (j < n && (i >= m || dp[i][j+1] >= dp[i+1][j])) {
      left.push({ lineNumA: null, lineNumB: null, type: 'added', content: '' });
      right.push({ lineNumA: null, lineNumB: lb++, type: 'added', content: linesB[j] });
      j++;
    } else {
      left.push({ lineNumA: la++, lineNumB: null, type: 'removed', content: linesA[i] });
      right.push({ lineNumA: null, lineNumB: null, type: 'removed', content: '' });
      i++;
    }
  }
  return { left, right };
}

function GitHubDiff({ result, versionA, versionB }: {
  result: ConflictResult;
  versionA: FileVersion | null;
  versionB: FileVersion | null;
}) {
  const [isAnimating, setIsAnimating] = React.useState(true);
  
  React.useEffect(() => {
    const timer = setTimeout(() => setIsAnimating(false), 600);
    return () => clearTimeout(timer);
  }, []);

  // Build sample diff from result.changes.diffs for demonstration
  const diffs = result.changes?.diffs || [];
  const linesA: string[] = [];
  const linesB: string[] = [];
  
  // Extract code from diffs to create side-by-side view
  diffs.forEach(d => {
    if (d.old_value) linesA.push(d.old_value);
    if (d.new_value) linesB.push(d.new_value);
  });

  const hasSources = linesA.length > 0 || linesB.length > 0;
  const { left, right } = hasSources ? buildSideBySideDiff(linesA, linesB) : { left: [], right: [] };

  const addedCount   = right.filter(l => l.type === 'added').length;
  const removedCount = left.filter(l => l.type === 'removed').length;
  const modifiedCount = left.filter(l => l.type === 'modified').length;

  if (!hasSources) {
    // Fallback: show diffs list in enhanced style
    return (
      <div className={`enhanced-diff-wrap ${isAnimating ? 'animating' : ''}`}>
        <div className="diff-header-enhanced">
          <div className="diff-versions">
            <div className="diff-ver-badge ver-a-badge">
              <Code2 size={14} />
              <span>Version {result.metadata?.versions?.version_a?.version_number || versionA?.version_number || 'A'}</span>
              <span className="ver-role">Reference</span>
            </div>
            <div className="diff-arrow-icon">
              <ArrowRight size={18} />
            </div>
            <div className="diff-ver-badge ver-b-badge">
              <Code2 size={14} />
              <span>Version {result.metadata?.versions?.version_b?.version_number || versionB?.version_number || 'B'}</span>
              <span className="ver-role">Modified</span>
            </div>
          </div>
          <div className="diff-stats-badges">
            <span className="stat-badge stat-add">+{result.summary?.stats?.lines_added || 0}</span>
            <span className="stat-badge stat-del">−{result.summary?.stats?.lines_deleted || 0}</span>
            <span className="stat-badge stat-mod">~{result.summary?.stats?.lines_modified || 0}</span>
          </div>
        </div>

        <div className="diff-file-container">
          <div className="diff-file-header">
            <FileCode size={16} />
            <span className="diff-filename">{result.metadata?.file?.file_name || 'Code Changes'}</span>
          </div>

          <div className="diff-split-container">
            {/* Left Panel - Version A */}
            <div className="diff-panel diff-panel-left">
              <div className="diff-panel-header">
                <span className="panel-title">Original Code</span>
                <span className="panel-badge">Version A</span>
              </div>
              <div className="diff-code-lines">
                {diffs.map((d, idx) => d.old_value && (
                  <div key={`a-${idx}`} className={`code-line-enhanced ${d.new_value ? 'line-modified' : 'line-removed'}`}>
                    <span className="line-num">{idx + 1}</span>
                    <span className="line-indicator">{d.new_value ? '~' : '−'}</span>
                    <pre className="line-content">{d.old_value}</pre>
                  </div>
                ))}
              </div>
            </div>

            {/* Divider */}
            <div className="diff-divider">
              <div className="divider-line" />
              <GitCompare size={20} className="divider-icon" />
              <div className="divider-line" />
            </div>

            {/* Right Panel - Version B */}
            <div className="diff-panel diff-panel-right">
              <div className="diff-panel-header">
                <span className="panel-title">Modified Code</span>
                <span className="panel-badge">Version B</span>
              </div>
              <div className="diff-code-lines">
                {diffs.map((d, idx) => d.new_value && (
                  <div key={`b-${idx}`} className={`code-line-enhanced ${d.old_value ? 'line-modified' : 'line-added'}`}>
                    <span className="line-num">{idx + 1}</span>
                    <span className="line-indicator">{d.old_value ? '~' : '+'}</span>
                    <pre className="line-content">{d.new_value}</pre>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="diff-legend-bar">
            <div className="legend-item legend-add">
              <Plus size={12} />
              <span>Added</span>
            </div>
            <div className="legend-item legend-del">
              <Minus size={12} />
              <span>Removed</span>
            </div>
            <div className="legend-item legend-mod">
              <Edit3 size={12} />
              <span>Modified</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`enhanced-diff-wrap ${isAnimating ? 'animating' : ''}`}>
      <div className="diff-header-enhanced">
        <div className="diff-versions">
          <div className="diff-ver-badge ver-a-badge">
            <Code2 size={14} />
            <span>Version {result.metadata?.versions?.version_a?.version_number || 'A'}</span>
            <span className="ver-role">Reference</span>
          </div>
          <div className="diff-arrow-icon">
            <ArrowRight size={18} />
          </div>
          <div className="diff-ver-badge ver-b-badge">
            <Code2 size={14} />
            <span>Version {result.metadata?.versions?.version_b?.version_number || 'B'}</span>
            <span className="ver-role">Modified</span>
          </div>
        </div>
        <div className="diff-stats-badges">
          <span className="stat-badge stat-add">+{addedCount}</span>
          <span className="stat-badge stat-del">−{removedCount}</span>
          {modifiedCount > 0 && <span className="stat-badge stat-mod">~{modifiedCount}</span>}
        </div>
      </div>

      <div className="diff-file-container">
        <div className="diff-file-header">
          <FileCode size={16} />
          <span className="diff-filename">{result.metadata?.file?.file_name || 'file'}</span>
        </div>

        <div className="diff-split-container">
          {/* Left Panel */}
          <div className="diff-panel diff-panel-left">
            <div className="diff-panel-header">
              <span className="panel-title">Original Code</span>
              <span className="panel-badge">Version A</span>
            </div>
            <div className="diff-code-lines">
              {left.map((line, idx) => (
                <div key={idx} className={`code-line-enhanced line-${line.type} ${line.highlight ? 'line-highlight' : ''}`}>
                  <span className="line-num">{line.lineNumA ?? ''}</span>
                  <span className="line-indicator">
                    {line.type === 'removed' ? '−' : line.type === 'modified' ? '~' : ' '}
                  </span>
                  <pre className="line-content">{line.content || ' '}</pre>
                </div>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="diff-divider">
            <div className="divider-line" />
            <GitCompare size={20} className="divider-icon" />
            <div className="divider-line" />
          </div>

          {/* Right Panel */}
          <div className="diff-panel diff-panel-right">
            <div className="diff-panel-header">
              <span className="panel-title">Modified Code</span>
              <span className="panel-badge">Version B</span>
            </div>
            <div className="diff-code-lines">
              {right.map((line, idx) => (
                <div key={idx} className={`code-line-enhanced line-${line.type} ${line.highlight ? 'line-highlight' : ''}`}>
                  <span className="line-num">{line.lineNumB ?? ''}</span>
                  <span className="line-indicator">
                    {line.type === 'added' ? '+' : line.type === 'modified' ? '~' : ' '}
                  </span>
                  <pre className="line-content">{line.content || ' '}</pre>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="diff-legend-bar">
          <div className="legend-item legend-add">
            <Plus size={12} />
            <span>Added</span>
          </div>
          <div className="legend-item legend-del">
            <Minus size={12} />
            <span>Removed</span>
          </div>
          <div className="legend-item legend-mod">
            <Edit3 size={12} />
            <span>Modified</span>
          </div>
        </div>
      </div>
    </div>
  );
}


function ConflictCard({ item }: { item: ConflictItem }) {
  return (
    <div className={`cd-conflict-item ${SEV[item.severity] ?? 'medium'}`}>
      <div className="cvc-conflict-header">
        <h4>{item.type} — {item.element?.name || 'Unknown'}()</h4>
        <span className={`cd-badge ${SEV[item.severity] ?? 'medium'}`}>{item.severity}</span>
      </div>
      <p>{item.description}</p>
      {(item.old_value || item.new_value) && (
        <div className="cvc-before-after">
          {item.old_value && (
            <div className="cvc-ba-col removed-bg">
              <div className="cvc-ba-label">Before</div><code>{item.old_value}</code>
            </div>
          )}
          {item.new_value && (
            <div className="cvc-ba-col added-bg">
              <div className="cvc-ba-label">After</div><code>{item.new_value}</code>
            </div>
          )}
        </div>
      )}
      {item.suggestion && <p className="cvc-impact">💡 {item.suggestion}</p>}
      {item.auto_fix_available && <span className="cvc-autofix-badge">✅ Auto-fix available</span>}
    </div>
  );
}

/* ─── Class Diagram Diff — Two-Column Side by Side ─── */
function ClassDiagramDiff({ result }: { result: ConflictResult }) {
  const diagramData = result.changes?.class_diagram_changes || {};
  const modified: any[] = diagramData.classes_modified || [];
  const added: any[]    = diagramData.classes_added    || [];
  const removed: any[]  = diagramData.classes_removed  || [];
  const unchanged: any[] = []; // classes_unchanged doesn't exist in the type

  const renderBox = (cls: any, side: 'a' | 'b') => {
    const isAdded    = cls.state === 'added';
    const isRemoved  = cls.state === 'removed';
    const isModified = cls.state === 'modified';
    return (
      <div key={`${cls.class_name}-${side}`}
        className={`uml2-box ${isAdded ? 'uml2-added' : isRemoved ? 'uml2-removed' : isModified ? 'uml2-modified' : ''}`}>
        <div className={`uml2-header ${isAdded ? 'uml2-h-added' : isRemoved ? 'uml2-h-removed' : isModified ? 'uml2-h-modified' : 'uml2-h-neutral'}`}>
          <span className="uml2-classname">{cls.class_name}</span>
          {isAdded   && <span className="uml2-badge uml2-badge-new">NEW</span>}
          {isRemoved && <span className="uml2-badge uml2-badge-del">DEL</span>}
        </div>
        <div className="uml2-body">
          {side === 'a' && isModified && <>
            {cls.methods_removed?.map((m: string) => <div key={m} className="uml2-member uml2-m-removed"><span className="uml2-sym">−</span>{m}</div>)}
            {cls.methods_modified?.map((m: string) => <div key={m} className="uml2-member uml2-m-modified"><span className="uml2-sym">±</span>{m}</div>)}
            {cls.methods_unchanged?.map((m: string) => <div key={m} className="uml2-member uml2-m-neutral"><span className="uml2-sym">+</span>{m}</div>)}
          </>}
          {side === 'b' && isModified && <>
            {cls.methods_added?.map((m: string) => <div key={m} className="uml2-member uml2-m-added"><span className="uml2-sym">+</span>{m}</div>)}
            {cls.methods_modified?.map((m: string) => <div key={m} className="uml2-member uml2-m-modified"><span className="uml2-sym">±</span>{m}</div>)}
            {cls.methods_unchanged?.map((m: string) => <div key={m} className="uml2-member uml2-m-neutral"><span className="uml2-sym">+</span>{m}</div>)}
          </>}
          {(isAdded || isRemoved) && cls.methods?.map((m: string) => (
            <div key={m} className={`uml2-member ${isAdded ? 'uml2-m-added' : 'uml2-m-removed'}`}>
              <span className="uml2-sym">{isAdded ? '+' : '−'}</span>{m}
            </div>
          ))}
          {!cls.methods_removed?.length && !cls.methods_added?.length && !cls.methods_modified?.length && !cls.methods?.length && (
            <div className="uml2-empty">—</div>
          )}
        </div>
      </div>
    );
  };

  const vA = [
    ...modified.map(c => ({ ...c, state: 'modified' })),
    ...removed.map(c => ({ ...c, state: 'removed' })),
  ];
  const vB = [
    ...modified.map(c => ({ ...c, state: 'modified' })),
    ...added.map(c => ({ ...c, state: 'added' })),
  ];
  const totalChanges =
    (result.summary?.stats?.methods_added    || 0) +
    (result.summary?.stats?.methods_removed  || 0) +
    (result.summary?.stats?.methods_modified || 0) +
    added.length + removed.length;

  return (
    <div className="uml2-wrap cd-animate">
      {/* Legend */}
      <div className="uml2-legend">
        <span className="uml2-leg-item"><span className="uml2-leg-dot uml2-dot-added"/>Added</span>
        <span className="uml2-leg-item"><span className="uml2-leg-dot uml2-dot-removed"/>Removed</span>
        <span className="uml2-leg-item"><span className="uml2-leg-dot uml2-dot-modified"/>Modified</span>
        <span className="uml2-leg-item"><span className="uml2-leg-dot uml2-dot-neutral"/>Unchanged</span>
      </div>

      <div className="uml2-columns">
        {/* Version A */}
        <div className="uml2-col">
          <div className="uml2-col-header uml2-col-a">
            <span>Version A</span><span className="uml2-col-role">Reference (Old)</span>
          </div>
          <div className="uml2-classes">
            {vA.map(c => renderBox(c, 'a'))}
            {unchanged.map((c: any) => (
              <div key={c.class_name || c} className="uml2-box">
                <div className="uml2-header uml2-h-neutral">
                  <span className="uml2-classname">{c.class_name || c}</span>
                </div>
              </div>
            ))}
            {vA.length === 0 && unchanged.length === 0 && <div className="uml2-no-changes">No changes</div>}
          </div>
        </div>

        {/* Divider Arrow */}
        <div className="uml2-divider">
          <div className="uml2-div-line"/>
          <ArrowRight size={16} color="#667eea"/>
          <div className="uml2-div-line"/>
        </div>

        {/* Version B */}
        <div className="uml2-col">
          <div className="uml2-col-header uml2-col-b">
            <span>Version B</span><span className="uml2-col-role">Comparison (New)</span>
          </div>
          <div className="uml2-classes">
            {vB.map(c => renderBox(c, 'b'))}
            {unchanged.map((c: any) => (
              <div key={c.class_name || c} className="uml2-box">
                <div className="uml2-header uml2-h-neutral">
                  <span className="uml2-classname">{c.class_name || c}</span>
                </div>
              </div>
            ))}
            {vB.length === 0 && unchanged.length === 0 && <div className="uml2-no-changes">No changes</div>}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="uml2-summary">
        <span className="uml2-sum added"><Plus size={11}/>{result.summary?.stats?.methods_added || 0} Added</span>
        <span className="uml2-sum removed"><Minus size={11}/>{result.summary?.stats?.methods_removed || 0} Removed</span>
        <span className="uml2-sum modified"><Edit3 size={11}/>{result.summary?.stats?.methods_modified || 0} Modified</span>
        <span className="uml2-sum total">{totalChanges} Total Changes</span>
      </div>
    </div>
  );
}

/* ─── Version Card ─── */
function VersionCard({ ver, selected, side, onClick }: {
  ver: FileVersion; selected: boolean; side: 'a' | 'b'; onClick: () => void;
}) {
  return (
    <div className={`vp-card ${selected ? (side === 'a' ? 'vp-sel-a' : 'vp-sel-b') : ''}`} onClick={onClick}>
      <div className="vp-dot" style={{ background: side === 'a' ? '#667eea' : '#10b981', opacity: selected ? 1 : 0.3 }}/>
      <div className="vp-info">
        <span className="vp-num">
          {ver.version_number}
          {ver.is_latest && <span className="vp-latest"><Star size={9}/> Latest</span>}
        </span>
        <span className="vp-date">{ver.created_at ? new Date(ver.created_at).toLocaleDateString('en') : ''}</span>
        {ver.status && <span className="vp-status">{ver.status}</span>}
      </div>
      {selected && <CheckCircle2 size={15} color="#5b21b6"/>}
    </div>
  );
}

/* ════════════════════ MAIN ════════════════════ */
const CodeVsCode: React.FC<Props> = ({ isOpen, onClose }) => {
  const [step, setStep]                       = useState<Step>('project');

  const [projects, setProjects]               = useState<UpmProject[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectsError, setProjectsError]     = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<UpmProject | null>(null);

  const [files, setFiles]                     = useState<ProjectFile[]>([]);
  const [filesLoading, setFilesLoading]       = useState(false);
  const [filesError, setFilesError]           = useState<string | null>(null);
  const [selectedFile, setSelectedFile]       = useState<ProjectFile | null>(null);
  const [fileSearch, setFileSearch]           = useState('');

  const [versions, setVersions]               = useState<FileVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionA, setVersionA]               = useState<FileVersion | null>(null);
  const [versionB, setVersionB]               = useState<FileVersion | null>(null);

  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analyzeStep, setAnalyzeStep]         = useState('');
  const [analyzeError, setAnalyzeError]       = useState<string | null>(null);

  const [result, setResult]                   = useState<ConflictResult | null>(null);
  const [resultTab, setResultTab]             = useState<ResultTab>('summary');

  const loadProjects = () => {
    setProjectsLoading(true); setProjectsError(null);
    fetchProjects().then(setProjects)
      .catch(e => setProjectsError(e.message ?? 'فشل تحميل المشاريع'))
      .finally(() => setProjectsLoading(false));
  };
  useEffect(() => { if (isOpen) loadProjects(); }, [isOpen]);

  const loadFiles = (id: string) => {
    setFilesLoading(true); setFilesError(null); setFiles([]);
    fetchProjectFiles(id).then(setFiles)
      .catch(e => setFilesError(e.message ?? 'فشل تحميل الملفات'))
      .finally(() => setFilesLoading(false));
  };

  const loadVersions = (id: string) => {
    setVersionsLoading(true); setVersions([]); setVersionA(null); setVersionB(null);
    fetchFileVersions(id).then(r => setVersions(r.history || []))
      .catch(() => setVersions([]))
      .finally(() => setVersionsLoading(false));
  };

  if (!isOpen) return null;

  const handleClose = () => {
    setStep('project');
    setSelectedProject(null); setSelectedFile(null);
    setFiles([]); setVersions([]); setVersionA(null); setVersionB(null);
    setResult(null); setAnalyzeError(null);
    setResultTab('summary'); setFileSearch('');
    onClose();
  };

  const handleAnalyzeVersions = async () => {
    if (!versionA || !versionB || !selectedProject) return;
    setAnalyzeError(null);
    setStep('analyzing'); setAnalyzeProgress(5);
    try {
      setAnalyzeStep('🚀 Initializing analysis engine...'); setAnalyzeProgress(15);
      await new Promise(r => setTimeout(r, 400)); // Smooth animation
      
      setAnalyzeStep('📊 Comparing code structures...'); setAnalyzeProgress(25);
      const { task_id } = await detectConflict({
        analysis_type: 'code_vs_code',
        project_id: selectedProject.id,
        file_id: selectedFile?.file_id || versionA.file_id,
        version_id_1: versionA.version_id,
        version_id_2: versionB.version_id,
        filepath: selectedFile?.filepath || versionA.filepath,
      });
      
      setAnalyzeProgress(40); setAnalyzeStep('🔍 Detecting conflicts...');
      await new Promise(r => setTimeout(r, 300));
      
      setAnalyzeProgress(55); setAnalyzeStep('⚡ Processing differences...');
      const reportId = await pollConflictStatus(task_id, {
        intervalMs: 2500, maxAttempts: 40,
        onProgress: (state, attempt) => {
          const progress = Math.min(55 + attempt * 2, 88);
          setAnalyzeProgress(progress);
          const emojis = ['🔄', '⚙️', '🎯', '💫'];
          setAnalyzeStep(`${emojis[attempt % 4]} ${state}...`);
        },
      });
      
      setAnalyzeProgress(92); setAnalyzeStep('✨ Generating insights...');
      await new Promise(r => setTimeout(r, 400));
      
      setAnalyzeProgress(97); setAnalyzeStep('📦 Fetching results...');
      const res = await fetchConflictResult(reportId);
      
      setAnalyzeProgress(100); setAnalyzeStep('✅ Analysis complete!');
      await new Promise(r => setTimeout(r, 500));
      
      setResult(res); setStep('result');
    } catch (err: unknown) {
      setAnalyzeError(err instanceof Error ? err.message : 'An error occurred');
      setStep('version-pick');
    }
  };

  const allConflicts: ConflictItem[] = result
    ? [...(result.conflicts?.structural || []), ...(result.conflicts?.semantic || []), ...(result.conflicts?.documentation || [])]
    : [];

  const stepLabels = ['Project', 'File', 'Versions', 'Results'];
  const stepKeys: Step[]  = ['project', 'file-pick', 'version-pick', 'result'];
  const currentIdx = stepKeys.indexOf(step === 'analyzing' ? 'result' : step);
  const filteredFiles = files.filter(f =>
    f.filename.toLowerCase().includes(fileSearch.toLowerCase()) ||
    f.filepath.toLowerCase().includes(fileSearch.toLowerCase())
  );

  return (
    <div className="cvc-overlay" onClick={handleClose}>
      <div className="cvc-modal" onClick={e => e.stopPropagation()}>

        {/* ══ HEADER ══ */}
        <div className="cvc-header">
          <div className="cvc-header-left">
            <div className="cvc-header-icon"><GitCompare size={18} color="#5b21b6"/></div>
            <div>
              <h2 className="cvc-title">Code vs Code</h2>
              <div className="cvc-steps">
                {stepLabels.map((s, i) => (
                  <React.Fragment key={s}>
                    <span className={`cvc-step-pill ${currentIdx === i ? 'active' : currentIdx > i ? 'done' : ''}`}>
                      {currentIdx > i ? <CheckCircle2 size={9}/> : <span className="cvc-step-num">{i+1}</span>}
                      {s}
                    </span>
                    {i < stepLabels.length-1 && <ChevronRight size={10} className="cvc-step-sep"/>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
          {selectedProject && (
            <div className="cvc-breadcrumb">
              <Folder size={11}/><span>{selectedProject.title}</span>
              {selectedFile && <><ChevronRight size={10}/><FileCode size={11}/><span>{selectedFile.filename}</span></>}
            </div>
          )}
          <button className="cvc-close" onClick={handleClose}><X size={16}/></button>
        </div>

        {/* ══ STEP 1 — PROJECT ══ */}
        {step === 'project' && (
          <div className="cvc-body cd-animate">
            <p className="cvc-section-label">Select Project</p>
            {projectsLoading && <div className="cvc-loading-row"><Loader2 size={18} className="cvc-spinner"/><span>Loading projects...</span></div>}
            {projectsError && (
              <div className="cvc-error-box">
                <AlertCircle size={16}/>{projectsError}
                <button className="cvc-retry-btn" onClick={loadProjects}><RefreshCw size={13}/>Retry</button>
              </div>
            )}
            {!projectsLoading && !projectsError && (
              <div className="cvc-project-grid">
                {projects.length === 0 && <p className="cvc-empty-note">No projects found.</p>}
                {projects.map(p => (
                  <div key={p.id}
                    className={`cvc-project-card ${selectedProject?.id === p.id ? 'selected' : ''}`}
                    onClick={() => setSelectedProject(p)}>
                    <div className="cvc-proj-icon">
                      {selectedProject?.id === p.id
                        ? <FolderOpen size={22} color="#a5b4fc"/>
                        : <Folder size={22} color="rgba(255,255,255,0.45)"/>}
                    </div>
                    <div className="cvc-proj-info">
                      <p className="cvc-proj-name">{p.title}</p>
                      <p className="cvc-proj-desc">{p.description || '—'}</p>
                      <div className="cvc-proj-meta">
                        <span className="cvc-proj-stat">{new Date(p.updated_at).toLocaleDateString('en')}</span>
                      </div>
                    </div>
                    {selectedProject?.id === p.id && <CheckCircle2 size={18} color="#5b21b6" className="cvc-proj-check"/>}
                  </div>
                ))}
              </div>
            )}
            <div className="cvc-step-footer">
              <span/>
              <button className="cvc-next-btn" disabled={!selectedProject} onClick={() => { loadFiles(selectedProject!.id); setStep('file-pick'); }}>
                Next — Select File <ArrowRight size={14}/>
              </button>
            </div>
          </div>
        )}

        {/* ══ STEP 2 — FILE PICKER ══ */}
        {step === 'file-pick' && (
          <div className="cvc-body cd-animate">
            <p className="cvc-section-label">Select File to Compare</p>
            <div className="cvc-search-wrap">
              <FileCode size={14} color="rgba(255,255,255,0.35)"/>
              <input className="cvc-search" placeholder="Search files..." value={fileSearch} onChange={e => setFileSearch(e.target.value)}/>
            </div>
            {filesLoading && <div className="cvc-loading-row"><Loader2 size={18} className="cvc-spinner"/><span>Loading files...</span></div>}
            {filesError && (
              <div className="cvc-error-box">
                <AlertCircle size={16}/>{filesError}
                <button className="cvc-retry-btn" onClick={() => loadFiles(selectedProject!.id)}><RefreshCw size={13}/>Retry</button>
              </div>
            )}
            {!filesLoading && !filesError && (
              <div className="cvc-file-list">
                {filteredFiles.length === 0 && <p className="cvc-empty-note">No matching files found.</p>}
                {filteredFiles.map(f => (
                  <div key={f.file_id}
                    className={`cvc-file-row ${selectedFile?.file_id === f.file_id ? 'selected' : ''}`}
                    onClick={() => setSelectedFile(f)}>
                    <div className="cvc-file-icon"><FileCode size={14} color="#a5b4fc"/></div>
                    <div className="cvc-file-info">
                      <span className="cvc-file-name">{f.filename}</span>
                      <span className="cvc-file-path">{f.filepath}</span>
                    </div>
                    <div className="cvc-file-meta">
                      {f.versions_count != null && <span className="cvc-ver-count"><GitBranch size={10}/> {f.versions_count} versions</span>}
                    </div>
                    {selectedFile?.file_id === f.file_id && <CheckCircle2 size={15} color="#5b21b6"/>}
                  </div>
                ))}
              </div>
            )}
            <div className="cvc-step-footer">
              <button className="cvc-back-btn" onClick={() => setStep('project')}>← Back</button>
              <button className="cvc-next-btn" disabled={!selectedFile}
                onClick={() => { loadVersions(selectedFile!.file_id); setStep('version-pick'); }}>
                Next — Select Versions <ArrowRight size={14}/>
              </button>
            </div>
          </div>
        )}

        {/* ══ STEP 4 — VERSION PICKER ══ */}
        {step === 'version-pick' && (
          <div className="cvc-body cd-animate">
            <div className="cvc-step-context">
              <FileCode size={13} color="#a5b4fc"/><span>{selectedFile?.filename}</span>
            </div>
            <p className="cvc-section-label" style={{ marginTop: 12 }}>Select Two Versions to Compare</p>
            {analyzeError && <div className="cvc-error-box"><AlertCircle size={16}/>{analyzeError}</div>}
            {versionsLoading && <div className="cvc-loading-row"><Loader2 size={18} className="cvc-spinner"/><span>Loading versions...</span></div>}
            {!versionsLoading && (
              <>
                <div className="vp-hint">Select <strong>Version A</strong> (reference) and <strong>Version B</strong> (comparison)</div>
                <div className="vp-columns">
                  <div className="vp-col">
                    <div className="vp-col-label ver-a">Version A <span className="vp-role">(Reference — Old)</span></div>
                    <div className="vp-list">
                      {versions.map(v => <VersionCard key={v.version_id} ver={v} selected={versionA?.version_id === v.version_id} side="a" onClick={() => setVersionA(v)}/>)}
                      {versions.length === 0 && <p className="cvc-empty-note">No versions found.</p>}
                    </div>
                  </div>
                  <div className="vp-arrow"><ArrowRight size={20} color="rgba(255,255,255,0.25)"/></div>
                  <div className="vp-col">
                    <div className="vp-col-label ver-b">Version B <span className="vp-role">(Comparison — New)</span></div>
                    <div className="vp-list">
                      {versions.map(v => <VersionCard key={v.version_id} ver={v} selected={versionB?.version_id === v.version_id} side="b" onClick={() => setVersionB(v)}/>)}
                      {versions.length === 0 && <p className="cvc-empty-note">No versions found.</p>}
                    </div>
                  </div>
                </div>
                {versionA && versionB && versionA.version_id === versionB.version_id && (
                  <div className="cvc-same-ver-warn">⚠️ Both versions are identical — Please select two different versions</div>
                )}
              </>
            )}
            <div className="cvc-step-footer">
              <button className="cvc-back-btn" onClick={() => setStep('file-pick')}>← Back</button>
              <button className="cvc-analyze-btn"
                disabled={!versionA || !versionB || versionA.version_id === versionB.version_id}
                onClick={handleAnalyzeVersions}>
                <GitCompare size={14}/> Start Analysis
              </button>
            </div>
          </div>
        )}

        {/* ══ ANALYZING ══ */}
        {step === 'analyzing' && (
          <div className="cvc-body cvc-analyzing-body cd-animate">
            <div className="cvc-progress-center">
              <div className="cvc-analyze-spinner-wrapper">
                <div className="spinner-orbit orbit-1" />
                <div className="spinner-orbit orbit-2" />
                <div className="spinner-orbit orbit-3" />
                <div className="cvc-analyze-spinner">
                  <Loader2 size={32} color="#667eea" className="cvc-spinner"/>
                </div>
              </div>
              <h3 className="cvc-analyzing-title">Analyzing Code Differences</h3>
              <p className="cvc-analyzing-sub">{analyzeStep}</p>
              <div className="cvc-progress-wrap" style={{ width: '100%', maxWidth: 420 }}>
                <div className="cvc-progress-bar">
                  <div className="cvc-progress-fill" style={{ width: `${analyzeProgress}%` }}>
                    <div className="progress-shimmer" />
                  </div>
                </div>
                <span className="cvc-progress-lbl">{analyzeProgress}%</span>
              </div>
              <div className="cvc-analyze-steps-list">
                {[
                  { label: 'Preparing Files', icon: '📁', threshold: 0 },
                  { label: 'Starting Analysis', icon: '🚀', threshold: 25 },
                  { label: 'Processing Conflicts', icon: '⚡', threshold: 50 },
                  { label: 'Fetching Results', icon: '✨', threshold: 75 }
                ].map((s) => {
                  const done   = analyzeProgress > s.threshold + 20;
                  const active = !done && analyzeProgress >= s.threshold;
                  return (
                    <div key={s.label} className={`cvc-analyze-step ${done ? 'done' : active ? 'active' : ''}`}>
                      <span className="step-icon">{s.icon}</span>
                      <span className="cvc-step-dot"/>
                      <span>{s.label}</span>
                      {done && <CheckCircle2 size={14} className="step-check" />}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ══ RESULT ══ */}
        {step === 'result' && result && (
          <div className="cvc-body cd-animate">
            <div className="cvc-result-context">
              <span className="cvc-ctx-item"><Folder size={12}/>{result.metadata?.project?.project_name || selectedProject?.title || 'Project'}</span>
              <ChevronRight size={11}/>
              <span className="cvc-ctx-item"><Code2 size={12}/>{result.metadata?.file?.file_name || selectedFile?.filename || 'File'}</span>
              <ChevronRight size={11}/>
              <span className="cvc-ctx-ver ver-a-text">{result.metadata?.versions?.version_a?.version_number || versionA?.version_number || 'vA'}</span>
              <ArrowRight size={11}/>
              <span className="cvc-ctx-ver ver-b-text">{result.metadata?.versions?.version_b?.version_number || versionB?.version_number || 'vB'}</span>
              <span style={{ marginLeft: 'auto', fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                {result.execution_time_seconds?.toFixed(1) || 0}s
              </span>
            </div>

            <div className="cvc-stats-row">
              <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary?.total_conflicts || 0}</div><div className="lbl">Conflicts</div></div>
              <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary?.breaking_changes || 0}</div><div className="lbl">Breaking</div></div>
              <div className="cd-stat"><div className="val" style={{ color: '#5b21b6' }}>{result.summary?.similarity_percentage || 0}%</div><div className="lbl">Similarity</div></div>
              <div className="cd-stat" style={{ display:'flex', alignItems:'center', justifyContent:'center' }}>
                <GradeCircle grade={result.summary?.grade || 'C'}/>
              </div>
            </div>

            {result.summary_text && <div className="cvc-summary-text">{result.summary_text}</div>}

            <div className="cd-legend" style={{ marginBottom: '1rem' }}>
              <span><span className="cd-legend-dot" style={{ background: '#10b981' }}/>Added</span>
              <span><span className="cd-legend-dot" style={{ background: '#ef4444' }}/>Removed</span>
              <span><span className="cd-legend-dot" style={{ background: '#f59e0b' }}/>Modified</span>
              <span><span className="cd-legend-dot" style={{ background: 'rgba(255,255,255,0.25)' }}/>Unchanged</span>
            </div>

            <div className="cd-tab-bar">
              {(['summary','diff','diagram','ai'] as ResultTab[]).map(t => (
                <button key={t} className={`cd-tab ${resultTab === t ? 'active' : ''}`} onClick={() => setResultTab(t)}>
                  {t === 'summary' ? 'Summary' : t === 'diff' ? 'Code Diff' : t === 'diagram' ? 'Class Diagram Diff' : 'AI Explanation'}
                </button>
              ))}
            </div>

            {resultTab === 'summary' && (
              <div className="cd-animate">
                <div className="cvc-stats-mini-grid">
                  {[
                    { l:'Lines Added',      v: result.summary?.stats?.lines_added     || 0, c:'#10b981' },
                    { l:'Lines Deleted',    v: result.summary?.stats?.lines_deleted    || 0, c:'#ef4444' },
                    { l:'Lines Modified',   v: result.summary?.stats?.lines_modified   || 0, c:'#f59e0b' },
                    { l:'Methods Added',    v: result.summary?.stats?.methods_added    || 0, c:'#10b981' },
                    { l:'Methods Removed',  v: result.summary?.stats?.methods_removed  || 0, c:'#ef4444' },
                    { l:'Methods Modified', v: result.summary?.stats?.methods_modified || 0, c:'#f59e0b' },
                  ].map(s => (
                    <div key={s.l} className="cvc-mini-stat">
                      <span className="cvc-mini-val" style={{ color: s.c }}>{s.v}</span>
                      <span className="cvc-mini-lbl">{s.l}</span>
                    </div>
                  ))}
                </div>
                <div className="cvc-conflicts">
                  {allConflicts.map((c, i) => <ConflictCard key={i} item={c}/>)}
                </div>
              </div>
            )}

            {resultTab === 'diff' && (
              <GitHubDiff result={result} versionA={versionA} versionB={versionB} />
            )}

            {resultTab === 'diagram' && <ClassDiagramDiff result={result}/>}

            {resultTab === 'ai' && (
              <div className="cvc-ai-view cd-animate">
                {result.suggestions?.map(s => (
                  <div key={s.suggestion_id} className={`cd-conflict-item ${SEV[s.priority] ?? 'medium'}`}>
                    <div className="cvc-conflict-header">
                      <h4>{s.title}</h4>
                      <span className={`cd-badge ${SEV[s.priority] ?? 'medium'}`}>{s.priority}</span>
                    </div>
                    <p>{s.description}</p>
                    <p className="cvc-impact">⏱ {s.estimated_effort}</p>
                    {s.auto_fix_available && <span className="cvc-autofix-badge">✅ Auto-fix available</span>}
                  </div>
                ))}
              </div>
            )}

            <div className="cvc-footer">
              <button className="cvc-back-btn" onClick={() => {
                setResult(null);
                setStep('version-pick');
              }}>← New Analysis</button>
              <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                <span style={{ fontSize:11, color:'rgba(255,255,255,0.4)' }}>ID: {result.analysis_id?.slice(-8) || 'N/A'}</span>
                <button className="cvc-export-btn">Export PDF</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default CodeVsCode;
