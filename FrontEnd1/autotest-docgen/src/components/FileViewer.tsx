import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Copy, FileText, AlertCircle, Loader, GitBranch,
  ChevronDown, FileOutput, Code, Zap,
} from 'lucide-react';
import type { FileNode } from './ProjectTree';
import apiService from '../services/api.service';

// ─── Types ────────────────────────────────────────────────────────────────────

interface FileContent {
  content: string; filename: string; filepath: string; file_type: string; size?: number;
}
interface DiagramClass {
  name: string;
  attributes?: { name: string; type: string; visibility: string }[];
  methods?: { name: string; signature: string; visibility: string; is_constructor: boolean }[];
  is_abstract?: boolean; is_interface?: boolean;
}
interface DiagramRelationship {
  from: string; to: string; type: string; label?: string; multiplicity?: string;
}
interface AnalysisResult {
  id: string; code_file_id: string; status: string;
  class_diagram_data?: { classes: DiagramClass[]; relationships: DiagramRelationship[] };
}
interface FileViewerProps {
  projectId: string; selectedNode: FileNode | null; isDarkMode: boolean;
}
type ViewMode = 'code' | 'diagram';
type ExplainLevel = 'high' | 'low';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getFileExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() || '';
}
function formatSize(bytes: number): string {
  if (!bytes) return '0 B';
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// ─── Syntax Highlighter ───────────────────────────────────────────────────────

function highlight(code: string, ext: string): string {
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  let h = esc(code);
  if (['py','js','ts','tsx','jsx','java','go','rs','rb','php','cs','kt'].includes(ext)) {
    h = h.replace(/(&quot;[^&]*?&quot;|&#39;[^&]*?&#39;|`[^`]*`)/g, '<span class="fv-str">$1</span>');
    h = h.replace(/(\/\/.*$|#.*$)/gm, '<span class="fv-cmt">$1</span>');
    h = h.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="fv-cmt">$1</span>');
    const kw = ext === 'py'
      ? 'def|class|import|from|return|if|elif|else|for|while|with|as|try|except|finally|pass|break|continue|lambda|yield|and|or|not|in|is|None|True|False|async|await'
      : 'import|export|from|const|let|var|function|return|if|else|for|while|class|interface|type|extends|implements|new|this|async|await|try|catch|throw|typeof|instanceof|default|switch|case|break|continue|public|private|protected|static|void|null|undefined|true|false';
    h = h.replace(new RegExp(`\\b(${kw})\\b`, 'g'), '<span class="fv-kw">$1</span>');
    h = h.replace(/\b(\d+\.?\d*)\b/g, '<span class="fv-num">$1</span>');
    h = h.replace(/\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()/g, '<span class="fv-fn">$1</span>');
  } else if (ext === 'json') {
    h = h.replace(/(&quot;[^&]*?&quot;)\s*:/g, '<span class="fv-fn">$1</span>:');
    h = h.replace(/:\s*(&quot;[^&]*?&quot;)/g, ': <span class="fv-str">$1</span>');
    h = h.replace(/:\s*(\d+\.?\d*)/g, ': <span class="fv-num">$1</span>');
    h = h.replace(/:\s*(true|false|null)/g, ': <span class="fv-kw">$1</span>');
  } else if (['html','xml','svg'].includes(ext)) {
    h = h.replace(/(&lt;\/?)([\w-]+)/g, '$1<span class="fv-kw">$2</span>');
    h = h.replace(/([\w-]+)=/g, '<span class="fv-fn">$1</span>=');
    h = h.replace(/(&quot;[^&]*?&quot;)/g, '<span class="fv-str">$1</span>');
  }
  return h;
}

// ─── Mermaid builder ─────────────────────────────────────────────────────────

function buildMermaid(classes: DiagramClass[], relationships: DiagramRelationship[]): string {
  const vis = (v: string) => ({ public: '+', private: '-', protected: '#', package: '~' }[v] ?? '+');
  const knownNames = new Set(classes.map(c => c.name.replace(/[^a-zA-Z0-9_]/g, '_')));
  let code = 'classDiagram\n';
  classes.forEach(cls => {
    const name = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
    code += `    class ${name} {\n`;
    if (cls.is_interface) code += `        <<interface>>\n`;
    else if (cls.is_abstract) code += `        <<abstract>>\n`;
    (cls.attributes || []).forEach(a => { code += `        ${vis(a.visibility)}${a.type} ${a.name}\n`; });
    (cls.methods || []).forEach(m => {
      const sig = m.signature || `${vis(m.visibility)}${m.name}()`;
      code += `        ${vis(m.visibility)}${sig.replace(/^[+\-#~]\s*/, '')}\n`;
    });
    code += `    }\n`;
  });
  const relMap: Record<string, string> = {
    inheritance: '<|--', implementation: '<|..', composition: '*--',
    aggregation: 'o--', association: '-->', dependency: '..>',
  };
  relationships.forEach(r => {
    const from = r.from.replace(/[^a-zA-Z0-9_]/g, '_');
    const to = r.to.replace(/[^a-zA-Z0-9_]/g, '_');
    if (!knownNames.has(from) || !knownNames.has(to)) return;
    const arrow = relMap[r.type] || '-->';
    const label = r.label ? ` : ${r.label}${r.multiplicity ? ' ' + r.multiplicity : ''}` : '';
    code += `    ${from} ${arrow} ${to}${label}\n`;
  });
  return code;
}

// ─── File Icon ────────────────────────────────────────────────────────────────

function getIconSvg(ext: string, size: number): React.ReactElement {
  const s = size;
  if (ext === 'py') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#3b82f6" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#3b82f6" fontFamily="monospace">Py</text></svg>;
  if (ext === 'js' || ext === 'jsx') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#f59e0b" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#f59e0b" fontFamily="monospace">JS</text></svg>;
  if (ext === 'ts' || ext === 'tsx') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#60a5fa" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#60a5fa" fontFamily="monospace">TS</text></svg>;
  if (ext === 'java') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#f97316" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#f97316" fontFamily="monospace">JAV</text></svg>;
  if (ext === 'go') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#06b6d4" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#06b6d4" fontFamily="monospace">Go</text></svg>;
  if (ext === 'json') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#f472b6" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#f472b6" fontFamily="monospace">{'{}'}</text></svg>;
  if (ext === 'md') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#60a5fa" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#60a5fa" fontFamily="monospace">MD</text></svg>;
  if (ext === 'pdf') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#ef4444" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#ef4444" fontFamily="monospace">PDF</text></svg>;
  if (ext === 'html' || ext === 'htm') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fb923c" fontFamily="monospace">HTM</text></svg>;
  if (ext === 'css') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#34d399" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#34d399" fontFamily="monospace">CSS</text></svg>;
  if (ext === 'xml') return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/><text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#fb923c" fontFamily="monospace">XML</text></svg>;
  if (['png','jpg','jpeg','gif','webp','ico'].includes(ext)) return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#a78bfa" opacity=".15"/><rect x="2" y="4" width="12" height="8" rx="1.5" stroke="#a78bfa" strokeWidth="1.2"/><circle cx="5.5" cy="7" r="1" fill="#a78bfa"/><path d="M2 11l3-3 2.5 2.5L10 8l4 4" stroke="#a78bfa" strokeWidth="1" strokeLinejoin="round"/></svg>;
  const label = ext ? ext.slice(0, 3).toUpperCase() : 'FILE';
  return <svg width={s} height={s} viewBox="0 0 16 16" fill="none"><rect width="16" height="16" rx="3" fill="#667eea" opacity=".12"/><text x="8" y="12" textAnchor="middle" fontSize={label.length > 2 ? '6.5' : '8'} fontWeight="700" fill="#667eea" fontFamily="monospace">{label}</text></svg>;
}

const FileIcon: React.FC<{ name: string; size?: number; colored?: boolean }> = ({ name, size = 16 }) =>
  getIconSvg(getFileExtension(name), size);

// ─── Class Diagram View ───────────────────────────────────────────────────────

const ClassDiagramView: React.FC<{ fileId: string | undefined; isDarkMode: boolean }> = ({ fileId, isDarkMode }) => {
  const [svg, setSvg] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fileId) return;
    setLoading(true); setError(null); setSvg('');
    fetch('/api/analysis/analysis-results/', { credentials: 'include' })
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((data: { results: AnalysisResult[] }) => {
        const match = (data.results || []).find(r => r.code_file_id === fileId);
        if (!match) throw new Error('No analysis found for this file');
        if (match.status !== 'COMPLETED') throw new Error(`Analysis status: ${match.status}`);
        const { classes, relationships } = match.class_diagram_data || { classes: [], relationships: [] };
        if (!classes?.length) throw new Error('No classes found in analysis');
        return buildMermaid(classes, relationships || []);
      })
      .then(mermaidCode =>
        import('mermaid').then(({ default: mermaid }) => {
          mermaid.initialize({ startOnLoad: false, theme: isDarkMode ? 'dark' : 'default', securityLevel: 'loose' });
          return mermaid.render(`fv-d-${Date.now()}`, mermaidCode);
        })
      )
      .then(({ svg: rendered }) => setSvg(rendered))
      .catch((e: any) => setError(e.message || 'Failed'))
      .finally(() => setLoading(false));
  }, [fileId, isDarkMode]);

  if (loading) return <div className="fv-center"><Loader size={22} className="fv-spin" /><span>Loading diagram…</span></div>;
  if (error) return <div className="fv-center fv-error"><AlertCircle size={22} /><span>{error}</span></div>;
  if (!svg) return <div className="fv-center fv-muted"><GitBranch size={36} strokeWidth={1} /><span>No diagram available</span></div>;
  return <div className="fv-diagram-wrap"><div className="fv-diagram-svg" dangerouslySetInnerHTML={{ __html: svg }} /></div>;
};

// ─── Main Component ───────────────────────────────────────────────────────────

const FileViewer: React.FC<FileViewerProps> = ({ projectId, selectedNode, isDarkMode }) => {
  // ── File content state ────────────────────────────────────────
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('code');
  const [explainLevel, setExplainLevel] = useState<ExplainLevel>('high');

  const loadContent = useCallback(async (node: FileNode) => {
    if (!projectId) return;
    setLoading(true); setError(null); setFileContent(null);
    try {
      const token = localStorage.getItem('access_token') || '';
      let url: string;
      if (node.id) {
        url = `/api/upm/projects/${projectId}/files/${node.id}/content/`;
      } else if (node.filepath && node.version_number !== undefined) {
        const p = new URLSearchParams({ filepath: node.filepath, version: String(node.version_number) });
        url = `/api/upm/projects/${projectId}/tree/file/?${p.toString()}`;
      } else if (node.filepath) {
        const p = new URLSearchParams({ filepath: node.filepath });
        url = `/api/upm/projects/${projectId}/tree/file/?${p.toString()}`;
      } else {
        throw new Error('Cannot determine file location');
      }
      const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setFileContent({
        content: data.content || '', filename: node.name,
        filepath: node.filepath || node.name,
        file_type: node.file_type || getFileExtension(node.name),
        size: data.size,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load file content');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (selectedNode) { setViewMode('code'); loadContent(selectedNode); }
    else { setFileContent(null); setError(null); }
  }, [selectedNode, loadContent]);

  // ── Logic / Export state ──────────────────────────────────────
  const [isProcessing, setIsProcessing] = useState(false);
  const [logicError, setLogicError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState(false);
  const [explanationText, setExplanationText] = useState<string | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  // wrapRef covers the entire Export dropdown (button + menu) so mousedown
  // on menu items does NOT close the dropdown before the click fires
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!exportOpen) return;
    const close = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setExportOpen(false);
      }
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [exportOpen]);

  // Reset all per-file state when the selected file changes
  useEffect(() => {
    setExplanationText(null);
    setLogicError(null);
    setIsProcessing(false);
    setExportOpen(false);
    setIsExporting(false);
    setSuccessToast(false);
  }, [selectedNode?.id]);

  const handleCopy = () => {
    if (!fileContent?.content) return;
    navigator.clipboard.writeText(fileContent.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // Resolve analysis_id: node first, then API fallback
  const resolveAnalysisId = async (): Promise<string> => {
    if (selectedNode?.analysis_result?.id) return selectedNode.analysis_result.id;
    const fileId = selectedNode?.id;
    if (!fileId) throw new Error('No file ID. Select a file first.');
    const res = await fetch(`/api/analysis/analysis-results/?code_file_id=${fileId}`, { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      const results: any[] = Array.isArray(data) ? data : (data.results || []);
      const match = results.find((r: any) => r.code_file_id === fileId || r.file_id === fileId);
      if (match?.id) return match.id;
    }
    const fb = await fetch('/api/analysis/analysis-results/', { credentials: 'include' });
    if (fb.ok) {
      const data = await fb.json();
      const results: any[] = Array.isArray(data) ? data : (data.results || []);
      const match = results.find((r: any) => r.code_file_id === fileId || r.file_id === fileId);
      if (match?.id) return match.id;
    }
    throw new Error('Analysis not found for this file. Run project analysis first.');
  };

  // Button 1: Generate Logic
  const handleGenerateLogic = async () => {
    setLogicError(null);
    setSuccessToast(false);
    setIsProcessing(true);
    try {
      const analysisId = await resolveAnalysisId();
      const genData = await apiService.analysis.generateExplanation({ analysis_id: analysisId, type: explainLevel });
      let expId: string = genData.analysis_id || analysisId;
      const taskId: string | undefined = genData.task_id;
      if (taskId) {
        for (let i = 0; i < 30; i++) {
          await new Promise(r => setTimeout(r, 3000));
          const s = await apiService.analysis.getTaskStatus(taskId);
          if (['SUCCESS', 'completed', 'COMPLETED'].includes(s.status)) { expId = s.analysis_id || expId; break; }
          if (['FAILURE', 'failed', 'FAILED'].includes(s.status)) throw new Error('Explanation generation failed.');
          if (i === 29) throw new Error('Timed out waiting for explanation.');
        }
      }
      setExplanationText(null);
      try {
        const typeParam = explainLevel === 'high' ? 'high_level' : 'low_level';
        const expRes = await fetch(
          `/api/analysis/ai-explanations/by-analysis/?analysis_id=${expId}&type=${typeParam}`,
          { credentials: 'include' }
        );
        if (expRes.ok) {
          const expData = await expRes.json();
          const text = expData.content || expData.explanation || expData.text;
          if (text) setExplanationText(text);
        }
      } catch (_) { /* non-critical */ }
      setSuccessToast(true);
      setTimeout(() => setSuccessToast(false), 4000);
    } catch (e: any) {
      setLogicError(e.message || 'Failed to generate logic explanation.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Button 2: Export Doc
  // URL: /api/analysis/export/{analysis_id}/?type=high|low&format=pdf|html|markdown|xml&mode=download
  const handleExport = async (fmt: 'pdf' | 'html' | 'markdown' | 'xml') => {
    setExportOpen(false);
    setLogicError(null);

    // Resolve analysis_id
    let analysisId: string | undefined = selectedNode?.analysis_result?.id;
    if (!analysisId) {
      try { analysisId = await resolveAnalysisId(); }
      catch (err: any) { setLogicError(err.message || 'Analysis not found. Run project analysis first.'); return; }
    }

    const exportUrl = 
`/api/analysis/export/${analysisId}/?type=${explainLevel}&format=${fmt}&mode=download`
;
    console.log('[Export] GET', exportUrl);

    setIsExporting(true);
    try {
      const res = await fetch(exportUrl, { credentials: 'include' });
      console.log('[Export] status:', res.status);
      if (!res.ok) {
        const errText = await res.text().catch(() => '');
        throw new Error(
`Export failed (${res.status})${errText ? ": " + errText.slice(0, 100) : ""}`
);
      }
      const blob = await res.blob();
      if (!blob || blob.size === 0) throw new Error('Server returned an empty file.');
      const extMap: Record<string, string> = { pdf: 'pdf', html: 'html', markdown: 'md', xml: 'xml' };
      const filename = 
`${selectedNode?.name ?? "doc"}_${explainLevel}.${extMap[fmt]}`
;
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl; a.download = filename; a.style.display = 'none';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(objectUrl), 10_000);
      console.log('[Export] downloaded:', filename);
    } catch (e: any) {
      console.error('[Export] failed:', e);
      setLogicError(e.message || 'Export failed.');
    } finally { setIsExporting(false); }
  };



  const ext = fileContent ? getFileExtension(fileContent.filename) : '';
  const lines = fileContent?.content.split('\n') || [];
  const fileExt = selectedNode ? getFileExtension(selectedNode.name).toUpperCase() : '';

  return (
    <div className={`fv-panel${isDarkMode ? ' dark' : ' light'}`}>

      {!selectedNode && (
        <div className="fv-empty">
          <FileText size={52} strokeWidth={1} className="fv-empty-icon" />
          <h3>No file selected</h3>
          <p>Click any file in the tree to view its contents</p>
        </div>
      )}

      {selectedNode && (
        <>
          {/* ── Control Bar ─────────────────────────────────────── */}
          <div className="fv-control-bar">

            {/* Left: file info */}
            <div className="fv-cb-file">
              <div className="fv-cb-file-icon"><FileIcon name={selectedNode.name} size={14} colored /></div>
              <span className="fv-cb-filename">{selectedNode.name}</span>
              {fileExt && <span className="fv-cb-badge">{fileExt}</span>}
              {fileContent && <span className="fv-cb-lines">{lines.length} lines</span>}
              {fileContent?.size !== undefined && <span className="fv-cb-lines">{formatSize(fileContent.size)}</span>}
            </div>

            {/* Right: controls */}
            <div className="fv-cb-controls">

              {/* View toggle */}
              <div className="fv-cb-label">View:</div>
              <div className="fv-toggle-group">
                <button className={`fv-toggle-btn${viewMode === 'code' ? ' active' : ''}`} onClick={() => setViewMode('code')}>
                  <Code size={13} /> Code
                </button>
                <button className={`fv-toggle-btn${viewMode === 'diagram' ? ' active' : ''}`} onClick={() => setViewMode('diagram')}>
                  <GitBranch size={13} /> Diagram
                </button>
              </div>

              {/* Copy — code mode only */}
              {viewMode === 'code' && (
                <button className={`fv-copy-btn${copied ? ' copied' : ''}`} onClick={handleCopy} disabled={!fileContent?.content}>
                  <Copy size={13} /> {copied ? 'Copied!' : 'Copy'}
                </button>
              )}

              {/* Level toggle */}
              <div className="fv-toggle-group">
                {(['high', 'low'] as ExplainLevel[]).map(lvl => (
                  <button key={lvl} className={`fv-toggle-btn${explainLevel === lvl ? ' active' : ''}`} onClick={() => setExplainLevel(lvl)}>
                    {lvl === 'high' ? 'High' : 'Low'}
                  </button>
                ))}
              </div>

              {/* Generate Logic — code mode only */}
              {viewMode === 'code' && (
                <div style={{ position: 'relative' }}>
                  <button className="fv-gen-btn" onClick={handleGenerateLogic} disabled={isProcessing} style={{ gap: 5 }}>
                    {isProcessing ? <Loader size={13} className="fv-spin" /> : <Zap size={13} />}
                    {isProcessing ? 'Generating…' : 'Generate Logic'}
                  </button>
                  {successToast && (
                    <div style={{ position: 'absolute', top: 'calc(100% + 4px)', right: 0, background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.30)', borderRadius: 8, padding: '5px 10px', fontSize: '0.72rem', color: '#6ee7b7', whiteSpace: 'nowrap', zIndex: 60, cursor: 'pointer' }}
                      onClick={() => setSuccessToast(false)}>
                      ✓ Logic generated! You can now export.
                    </div>
                  )}
                  {logicError && !isProcessing && !isExporting && (
                    <div style={{ position: 'absolute', top: 'calc(100% + 4px)', right: 0, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.30)', borderRadius: 8, padding: '5px 10px', fontSize: '0.72rem', color: '#fca5a5', whiteSpace: 'nowrap', zIndex: 60, maxWidth: 300, cursor: 'pointer' }}
                      onClick={() => setLogicError(null)}>
                      ⚠ {logicError}
                    </div>
                  )}
                </div>
              )}

              {/* Export dropdown — wrapRef covers button + menu so mousedown
                  on menu items does NOT close the dropdown before click fires */}
              <div className="fv-gen-wrap" ref={wrapRef}>
                <button
                  className="fv-gen-btn"
                  onClick={() => !isExporting && setExportOpen(o => !o)}
                  disabled={isExporting}
                >
                  {isExporting ? <Loader size={13} className="fv-spin" /> : <FileOutput size={13} />}
                  {isExporting ? 'Exporting…' : 'Export Doc'}
                  {!isExporting && <ChevronDown size={12} className={`fv-gen-arrow${exportOpen ? ' open' : ''}`} />}
                </button>

                {logicError && !isProcessing && isExporting && (
                  <div style={{ position: 'absolute', top: 'calc(100% + 4px)', right: 0, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.30)', borderRadius: 8, padding: '5px 10px', fontSize: '0.72rem', color: '#fca5a5', whiteSpace: 'nowrap', zIndex: 60, maxWidth: 300, cursor: 'pointer' }}
                    onClick={() => setLogicError(null)}>
                    ⚠ {logicError}
                  </div>
                )}

                {exportOpen && (
                  <div className="fv-gen-menu">
                    <button className="fv-gen-item" onClick={() => handleExport('pdf')}>
                      <span className="fv-gen-fmt fv-fmt-pdf">PDF</span> PDF Document
                    </button>
                    <button className="fv-gen-item" onClick={() => handleExport('html')}>
                      <span className="fv-gen-fmt" style={{ background: 'rgba(251,146,60,0.15)', color: '#fb923c' }}>HTM</span> HTML
                    </button>
                    <button className="fv-gen-item" onClick={() => handleExport('markdown')}>
                      <span className="fv-gen-fmt fv-fmt-md">MD</span> Markdown
                    </button>
                    <button className="fv-gen-item" onClick={() => handleExport('xml')}>
                      <span className="fv-gen-fmt" style={{ background: 'rgba(251,146,60,0.15)', color: '#fb923c' }}>XML</span> XML
                    </button>
                  </div>
                )}
              </div>

            </div>
          </div>

          {/* ── Content ─────────────────────────────────────────── */}
          <div className="fv-body">

            {viewMode === 'code' && (
              <>
                {loading && <div className="fv-center"><Loader size={20} className="fv-spin" /><span>Loading…</span></div>}
                {!loading && error && (
                  <div className="fv-center fv-error">
                    <AlertCircle size={20} /><span>{error}</span>
                    <button className="fv-retry-btn" onClick={() => selectedNode && loadContent(selectedNode)}>Retry</button>
                  </div>
                )}
                {!loading && !error && fileContent && (
                  <div className="fv-split-view">
                    <div className="fv-code-wrap">
                      <div className="fv-line-nums" aria-hidden="true">
                        {lines.map((_, i) => <span key={i} className="fv-line-num">{i + 1}</span>)}
                      </div>
                      <pre className="fv-code">
                        <code dangerouslySetInnerHTML={{ __html: highlight(fileContent.content, ext) }} />
                      </pre>
                    </div>
                    {(isProcessing || explanationText) && (
                      <div className={`fv-explanation-pane${isDarkMode ? ' dark' : ' light'}`}>
                        <div className="fv-explanation-header">
                          <Zap size={13} style={{ opacity: 0.7 }} />
                          <span>AI Explanation</span>
                          <span className="fv-explanation-level">{explainLevel === 'high' ? 'High-level' : 'Low-level'}</span>
                          {explanationText && (
                            <button className="fv-explanation-close" onClick={() => setExplanationText(null)} title="Dismiss">×</button>
                          )}
                        </div>
                        <div className="fv-explanation-body">
                          {isProcessing && !explanationText && (
                            <div className="fv-center" style={{ padding: '24px 0' }}>
                              <Loader size={18} className="fv-spin" />
                              <span style={{ marginLeft: 8, fontSize: '0.82rem' }}>Generating explanation…</span>
                            </div>
                          )}
                          {explanationText && <pre className="fv-explanation-text">{explanationText}</pre>}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {viewMode === 'diagram' && (
              <ClassDiagramView fileId={selectedNode.id} isDarkMode={isDarkMode} />
            )}

          </div>
        </>
      )}
    </div>
  );
};

export default FileViewer;
