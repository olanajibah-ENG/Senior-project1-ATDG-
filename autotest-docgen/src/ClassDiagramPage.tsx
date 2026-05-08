import React, { useRef, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, Layers, AlertCircle, Zap, FileText,
  Loader, CheckCircle, Sun, Moon, ZoomIn, ZoomOut, Maximize2,
  ChevronDown,
} from 'lucide-react';
import { useLanguage } from './context/LanguageContext';
import './DocumentGenerationPage.css';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DiagramAttribute {
  name: string; type: string;
  visibility: 'public' | 'private' | 'protected' | 'package';
}
interface MethodParameter { name: string; type: string; }
interface DiagramMethod {
  name: string; parameters: MethodParameter[]; return_type: string;
  visibility: 'public' | 'private' | 'protected' | 'package';
  type: 'constructor' | 'method';
}
interface DiagramClass {
  name: string; attributes?: DiagramAttribute[]; methods?: DiagramMethod[];
  is_abstract?: boolean; is_interface?: boolean;
}
interface ClassRelationship {
  from: string; to: string;
  type: 'inheritance' | 'implementation' | 'composition' | 'aggregation' | 'association' | 'dependency';
  label?: string;
}
interface DiagramLocationState {
  projectId: string; codeName: string; fileName: string;
  isProjectDiagram?: boolean; analysisIds?: string[];
  fromFileTree?: boolean; explanationLevel?: 'high' | 'low';
  diagram: { title?: string; classes?: DiagramClass[]; relationships?: ClassRelationship[]; };
}

type DocFormat = 'pdf' | 'md' | 'html' | 'xml';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const getCsrf = () => {
  const cookies = document.cookie.split(';').map(c => c.trim());
  const t =
    cookies.find(c => c.startsWith('ai_csrftoken='))?.split('=')[1] ||
    cookies.find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
  return decodeURIComponent(t);
};

// ─── Component ────────────────────────────────────────────────────────────────

const ClassDiagramPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language } = useLanguage();
  const isRTL = language === 'ar';
  const diagramRef = useRef<HTMLDivElement>(null);

  // ── Theme ──
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // ── Diagram ──
  const [mermaidSvg, setMermaidSvg] = useState('');
  const [isDiagramReady, setIsDiagramReady] = useState(false);
  const [diagramError, setDiagramError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

  // ── Export image ──
  const [isExporting, setIsExporting] = useState(false);

  // ── Explanation ──
  const [isGeneratingExplanation, setIsGeneratingExplanation] = useState(false);
  const [explanationDone, setExplanationDone] = useState(false);
  const [explanationAnalysisId, setExplanationAnalysisId] = useState<string | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  // ── Document export ──
  const [isExportingDocument, setIsExportingDocument] = useState(false);
  const [showDocDropdown, setShowDocDropdown] = useState(false);

  // ── State from navigation ──
  const state = (location.state || {}) as DiagramLocationState;
  const { codeName, diagram, isProjectDiagram, analysisIds, fromFileTree, explanationLevel } = state;

  const [explanationType, setExplanationType] = useState<'high_level' | 'low_level'>(
    explanationLevel === 'low' ? 'low_level' : 'high_level'
  );

  const canGenerate = isProjectDiagram || fromFileTree;

  // ── Resolve project analysis ID on mount if not passed via navigation ──
  // This covers the case where the page is reached from Dashboard (not ProjectTree)
  // and analysisIds was not populated by the caller.
  const [resolvedAnalysisId, setResolvedAnalysisId] = useState<string | null>(
    analysisIds?.[0] ?? null
  );

  useEffect(() => {
    // Already have it — nothing to do
    if (resolvedAnalysisId) return;
    // Only attempt resolution for project-level pages
    if (!canGenerate || !state.projectId) return;

    const token = localStorage.getItem('access_token') || '';
    fetch(`/api/analysis/analyze-project/?project_id=${state.projectId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => {
        const ids: string[] = data.analysis_ids || [];
        if (ids.length > 0) setResolvedAnalysisId(ids[0]);
      })
      .catch(() => { /* no analysis yet — user will see error when they click Generate */ });
  }, [state.projectId, canGenerate]);

  // ── Close doc dropdown on outside click ──
  useEffect(() => {
    if (!showDocDropdown) return;
    const close = () => setShowDocDropdown(false);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [showDocDropdown]);

  // ── Sync dark mode ──
  useEffect(() => {
    document.body.classList.toggle('dark-mode', isDarkMode);
  }, [isDarkMode]);

  // ─── Mermaid helpers ──────────────────────────────────────────────────────────

  const getVisibilitySymbol = (v: string) =>
    ({ public: '+', private: '-', protected: '#', package: '~' }[v] ?? '+');

  const cleanType = (t: string) =>
    t.replace(/</g, '~').replace(/>/g, '~').replace(/[^a-zA-Z0-9_~[\]]/g, '_');

  const buildMermaidCode = (): string => {
    if (!diagram?.classes?.length) return '';
    const known = new Set((diagram.classes || []).map(c => c.name.replace(/[^a-zA-Z0-9_]/g, '_')));
    let code = 'classDiagram\n';
    diagram.classes.forEach(cls => {
      const name = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
      code += `    class ${name} {\n`;
      if (cls.is_interface) code += `        <<interface>>\n`;
      else if (cls.is_abstract) code += `        <<abstract>>\n`;
      (cls.attributes || []).forEach(a =>
        code += `        ${getVisibilitySymbol(a.visibility)}${cleanType(a.type)} ${a.name}\n`
      );
      (cls.methods || []).forEach(m => {
        const params = (m.parameters || []).map(p => `${p.name} ${cleanType(p.type)}`).join(', ');
        const ret = m.return_type && m.return_type !== 'void' ? ` ${cleanType(m.return_type)}` : '';
        code += `        ${getVisibilitySymbol(m.visibility)}${m.name}(${params})${ret}\n`;
      });
      code += `    }\n`;
    });
    (diagram.relationships || []).forEach(rel => {
      const from = rel.from.replace(/[^a-zA-Z0-9_]/g, '_');
      const to = rel.to.replace(/[^a-zA-Z0-9_]/g, '_');
      if (!known.has(to)) return;
      const label = rel.label ? ` : ${rel.label}` : '';
      const arrows: Record<string, string> = {
        inheritance: `${from} --|> ${to}${label}`,
        implementation: `${from} ..|> ${to}${label}`,
        composition: `${from} *-- ${to}${label}`,
        aggregation: `${from} o-- ${to}${label}`,
        dependency: `${from} ..> ${to}${label}`,
        association: `${from} --> ${to}${label}`,
      };
      code += `    ${arrows[rel.type] ?? `${from} --> ${to}${label}`}\n`;
    });
    return code;
  };

  // ─── Render Mermaid ───────────────────────────────────────────────────────────

  useEffect(() => {
    if (!diagram?.classes?.length) return;
    const generate = async () => {
      try {
        const mermaid = (await import('mermaid')).default;
        const darkVars = {
          primaryColor: '#1a1a2e', primaryTextColor: '#e2d9f3',
          primaryBorderColor: '#e879f9', lineColor: '#e879f9',
          secondaryColor: '#16213e', tertiaryColor: '#0f3460',
          edgeLabelBackground: '#1a1a2e', titleColor: '#e2d9f3',
          attributeBackgroundColorEven: '#16213e', attributeBackgroundColorOdd: '#1a1a2e',
          classText: '#e2d9f3', nodeBorder: '#e879f9',
          mainBkg: '#1a1a2e', nodeBkg: '#1a1a2e', clusterBkg: '#0f0a1e',
          defaultLinkColor: '#e879f9', fontFamily: 'Inter, sans-serif', fontSize: '14px',
          labelBackground: '#1a1a2e', labelTextColor: '#e2d9f3',
          background: '#0f0a1e', textColor: '#e2d9f3',
        };
        const lightVars = {
          primaryColor: '#f3e8ff', primaryTextColor: '#1a202c',
          primaryBorderColor: '#4c1d95', lineColor: '#4c1d95',
          secondaryColor: '#e9d8fd', tertiaryColor: '#faf5ff',
          edgeLabelBackground: '#f3e8ff', titleColor: '#4c1d95',
          classText: '#1a202c', nodeBorder: '#4c1d95',
          mainBkg: '#f3e8ff', nodeBkg: '#f3e8ff',
        };
        mermaid.initialize({
          startOnLoad: false, theme: 'base', securityLevel: 'loose',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          themeVariables: isDarkMode ? darkVars : lightVars,
        } as any);
        const code = buildMermaidCode();
        const { svg } = await mermaid.render(`diagram-${Date.now()}`, code);
        setMermaidSvg(svg);
        setIsDiagramReady(true);
        setDiagramError(null);
      } catch (e: any) {
        setDiagramError(e?.message || 'Failed to render diagram');
        setIsDiagramReady(false);
      }
    };
    generate();
  }, [diagram, isDarkMode]);

  // ─── Generate Explanation ─────────────────────────────────────────────────────

  const handleGenerateExplanation = async () => {
    if (isGeneratingExplanation) return;
    // Use the resolved project-level analysis ID.
    // resolvedAnalysisId is populated either from navigation state (analysisIds[0])
    // or by fetching /api/analysis/analyze-project/?project_id=... on mount.
    // NEVER use state.projectId — that is a UPM project UUID, not an analysis result ID.
    const targetId = resolvedAnalysisId;
    if (!targetId) {
      setExplanationError(
        isRTL
          ? 'لا يوجد معرّف تحليل. يرجى توليد مخطط الكلاسات أولاً.'
          : 'No analysis ID found. Please generate the class diagram first.'
      );
      return;
    }
    setIsGeneratingExplanation(true);
    setExplanationError(null);
    setExplanationDone(false);
    try {
      const res = await fetch('/api/analysis/ai-explanations/generate-explanation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        credentials: 'include',
        body: JSON.stringify({
          analysis_id: targetId,
          type: explanationType === 'high_level' ? 'high' : 'low',
        }),
      });
      if (!res.ok) {
        const txt = await res.text().catch(() => '');
        throw new Error(`${res.status}${txt ? ' — ' + txt.slice(0, 120) : ''}`);
      }
      const result = await res.json();
      const taskId = result.task_id;
      const expId = result.analysis_id || targetId;
      if (taskId) {
        for (let i = 1; i <= 30; i++) {
          await new Promise(r => setTimeout(r, 3000));
          try {
            const sRes = await fetch(
              `/api/analysis/ai-explanations/task-status/?task_id=${taskId}`,
              { credentials: 'include' }
            );
            if (!sRes.ok) continue;
            const s = await sRes.json();
            if (['SUCCESS', 'completed', 'COMPLETED'].includes(s.status)) {
              setExplanationAnalysisId(expId); setExplanationDone(true); break;
            } else if (['FAILURE', 'failed'].includes(s.status)) {
              throw new Error('Explanation generation failed.');
            }
          } catch (e) { if (i === 30) throw e; }
        }
      } else {
        setExplanationAnalysisId(expId); setExplanationDone(true);
      }
    } catch (err: any) {
      setExplanationError(err.message || 'Failed to generate explanation');
    } finally {
      setIsGeneratingExplanation(false);
    }
  };

  // ─── Export Document ──────────────────────────────────────────────────────────

  const handleExportDocument = async (fmt: DocFormat) => {
    if (!explanationDone || !explanationAnalysisId || isExportingDocument) return;
    setIsExportingDocument(true);
    setShowDocDropdown(false);
    try {
      const type = explanationType === 'high_level' ? 'high' : 'low';
      // Use /api/analysis/export/{id}/ — this endpoint handles both ObjectId and project UUID
      // export-legacy only accepts ObjectId, but explanationAnalysisId may be a project UUID
      const params = new URLSearchParams({ type, format: fmt });
      const res = await fetch(
        `/api/analysis/export/${explanationAnalysisId}/?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      const blob = await res.blob();
      if (blob.size === 0) throw new Error('Downloaded file is empty');
      const extMap: Record<DocFormat, string> = { pdf: 'pdf', md: 'md', html: 'html', xml: 'xml' };
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${codeName || 'project'}_${type}.${extMap[fmt]}`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setIsExportingDocument(false);
    }
  };

  // ─── Export SVG ───────────────────────────────────────────────────────────────

  const handleExportSVG = () => {
    if (!diagramRef.current || !isDiagramReady) return;
    const svgEl = diagramRef.current.querySelector('svg');
    if (!svgEl) return;
    const blob = new Blob([new XMLSerializer().serializeToString(svgEl)], { type: 'image/svg+xml;charset=utf-8' });
    const a = document.createElement('a');
    a.download = `${(codeName || 'diagram').replace(/\s+/g, '_')}_class_diagram.svg`;
    a.href = URL.createObjectURL(blob);
    a.click();
    URL.revokeObjectURL(a.href);
  };

  // ─── Export PNG ───────────────────────────────────────────────────────────────

  const handleExportPNG = async () => {
    if (!diagramRef.current || !isDiagramReady) return;
    setIsExporting(true);
    try {
      const svgEl = diagramRef.current.querySelector('svg');
      if (!svgEl) throw new Error('SVG not found');
      const vb = svgEl.getAttribute('viewBox')?.split(' ').map(Number) || [];
      const svgW = vb[2] || svgEl.clientWidth || 1200;
      const svgH = vb[3] || svgEl.clientHeight || 900;
      const clone = svgEl.cloneNode(true) as SVGElement;
      clone.setAttribute('width', String(svgW));
      clone.setAttribute('height', String(svgH));
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      clone.querySelectorAll('foreignObject').forEach(fo => {
        const parent = fo.parentNode; if (!parent) return;
        const foX = parseFloat(fo.getAttribute('x') || '0');
        const foY = parseFloat(fo.getAttribute('y') || '0');
        const foW = parseFloat(fo.getAttribute('width') || '80');
        const foH = parseFloat(fo.getAttribute('height') || '20');
        const text = fo.textContent?.replace(/\s+/g, ' ').trim() || '';
        if (!text) { fo.remove(); return; }
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', String(foX + foW / 2));
        textEl.setAttribute('y', String(foY + foH / 2 + 4));
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'middle');
        textEl.setAttribute('fill', isDarkMode ? '#e2d9f3' : '#1a202c');
        textEl.setAttribute('font-family', 'Arial, sans-serif');
        textEl.setAttribute('font-size', '13');
        textEl.textContent = text;
        parent.replaceChild(textEl, fo);
      });
      if (isDarkMode) {
        clone.querySelectorAll('rect').forEach(r => {
          if (r.getAttribute('width') === '100%') { r.setAttribute('fill', '#0f0a1e'); return; }
          r.setAttribute('fill', '#1a1a2e'); r.setAttribute('stroke', '#e879f9');
        });
        clone.querySelectorAll('text, tspan').forEach(t => t.setAttribute('fill', '#e2d9f3'));
        clone.querySelectorAll('.edgePath path, .relation').forEach(p => {
          p.setAttribute('stroke', '#e879f9'); p.setAttribute('stroke-width', '2.5');
        });
        clone.querySelectorAll('marker path, marker polygon').forEach(m => {
          m.setAttribute('fill', '#e879f9'); m.setAttribute('stroke', '#e879f9');
        });
        clone.querySelectorAll('line').forEach(l => l.setAttribute('stroke', '#e879f9'));
      } else {
        clone.querySelectorAll('.edgePath path, .relation').forEach(p => {
          p.setAttribute('stroke', '#4c1d95'); p.setAttribute('stroke-width', '2');
        });
        clone.querySelectorAll('marker path, marker polygon').forEach(m => {
          m.setAttribute('fill', '#4c1d95'); m.setAttribute('stroke', '#4c1d95');
        });
      }
      const svgStr = new XMLSerializer().serializeToString(clone);
      const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const scale = 2;
      const canvas = document.createElement('canvas');
      canvas.width = svgW * scale; canvas.height = svgH * scale;
      const ctx = canvas.getContext('2d')!;
      ctx.fillStyle = isDarkMode ? '#0f0a1e' : '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);
      const img = new window.Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, svgW, svgH);
        URL.revokeObjectURL(url);
        canvas.toBlob(pngBlob => {
          if (pngBlob) {
            const a = document.createElement('a');
            a.download = `${(codeName || 'diagram').replace(/\s+/g, '_')}_class_diagram.png`;
            a.href = URL.createObjectURL(pngBlob);
            document.body.appendChild(a); a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 200);
          }
          setIsExporting(false);
        }, 'image/png', 1.0);
      };
      img.onerror = () => { URL.revokeObjectURL(url); setIsExporting(false); };
      img.src = url;
    } catch (e) {
      console.error('PNG export error:', e);
      setIsExporting(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────────────────

  const D = isDarkMode;

  return (
    <div className={`cdp-page ${D ? 'dark' : 'light'}`} dir={isRTL ? 'rtl' : 'ltr'}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header className="cdp-header">

        {/* Left: back + title */}
        <div className="cdp-header-left">
          <button
            className="cdp-back-btn"
            onClick={() => fromFileTree && state.projectId
              ? navigate(`/dashboard/projects/${state.projectId}/tree`)
              : navigate('/dashboard')
            }
          >
            <ArrowLeft size={16} />
            {fromFileTree ? (isRTL ? 'شجرة الملفات' : 'File Tree') : (isRTL ? 'رجوع' : 'Back')}
          </button>

          <div className="cdp-header-title">
            <Layers size={18} />
            <span>{codeName || (isRTL ? 'مخطط الكلاسات' : 'Class Diagram')}</span>
          </div>
        </div>

        {/* Right: all controls */}
        <div className="cdp-header-controls">

          {/* ── Level + Generate + Document — single row ── */}
          {canGenerate && (
            <div className="cdp-controls-row">

              {/* Level label */}
              <span className="cdp-row-label">
                <Zap size={12} />
                {isRTL ? 'المستوى' : 'Level'}
              </span>

              {/* High / Low toggle */}
              <div className="cdp-toggle-pair">
                {(['high_level', 'low_level'] as const).map(val => (
                  <button
                    key={val}
                    className={`cdp-toggle-btn${explanationType === val ? ' active' : ''}`}
                    onClick={() => setExplanationType(val)}
                    disabled={isGeneratingExplanation || explanationDone}
                  >
                    {val === 'high_level'
                      ? (isRTL ? 'عالي' : 'High')
                      : (isRTL ? 'منخفض' : 'Low')}
                  </button>
                ))}
              </div>

              {/* Divider */}
              <div className="cdp-row-divider" />

              {/* Generate button */}
              <button
                className={`cdp-action-btn${explanationDone ? ' success' : ''}`}
                onClick={handleGenerateExplanation}
                disabled={isGeneratingExplanation || explanationDone}
              >
                {isGeneratingExplanation
                  ? <><Loader size={14} className="cdp-spin" />{isRTL ? 'جاري...' : 'Generating...'}</>
                  : explanationDone
                    ? <><CheckCircle size={14} />{isRTL ? 'جاهز' : 'Generated'}</>
                    : <><Zap size={14} />{isRTL ? 'توليد شرح' : 'Generate'}</>
                }
              </button>

              {/* Divider */}
              <div className="cdp-row-divider" />

              {/* Document dropdown */}
              <div className="cdp-dropdown-wrap" onClick={e => e.stopPropagation()}>
                <button
                  className={`cdp-action-btn cdp-dropdown-trigger${!explanationDone ? ' muted' : ''}`}
                  onClick={() => explanationDone && setShowDocDropdown(d => !d)}
                  disabled={isExportingDocument || !explanationDone}
                  title={!explanationDone ? (isRTL ? 'ولّد الشرح أولاً' : 'Generate first') : ''}
                >
                  {isExportingDocument
                    ? <><Loader size={14} className="cdp-spin" />{isRTL ? 'جاري...' : 'Exporting...'}</>
                    : <><FileText size={14} />{isRTL ? 'تنزيل' : 'Download'}<ChevronDown size={11} className={showDocDropdown ? 'cdp-chevron-open' : ''} /></>
                  }
                </button>
                {showDocDropdown && (
                  <div className="cdp-dropdown-menu">
                    {([
                      { fmt: 'pdf' as DocFormat, label: 'PDF',      color: '#ef4444' },
                      { fmt: 'html' as DocFormat, label: 'HTML',     color: '#fb923c' },
                      { fmt: 'md' as DocFormat,   label: 'Markdown', color: '#3b82f6' },
                      { fmt: 'xml' as DocFormat,  label: 'XML',      color: '#fb923c' },
                    ]).map(({ fmt, label, color }) => (
                      <button key={fmt} className="cdp-dropdown-item" onClick={() => handleExportDocument(fmt)}>
                        <span className="cdp-fmt-badge" style={{ background: `${color}22`, color }}>{fmt.toUpperCase()}</span>
                        {label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}

          {/* ── Theme toggle ── */}
          <button
            className="cdp-mode-btn"
            onClick={() => setIsDarkMode(d => { localStorage.setItem('theme', !d ? 'dark' : 'light'); return !d; })}
            title={D ? 'Light Mode' : 'Dark Mode'}
          >
            {D ? <Sun size={16} /> : <Moon size={16} />}
          </button>

        </div>
      </header>

      {/* ── Main content ────────────────────────────────────────────────────── */}
      <main className="cdp-content">

        {/* Explanation error */}
        {explanationError && (
          <div className="cdp-error-banner">
            <AlertCircle size={16} />
            <span>{explanationError}</span>
          </div>
        )}

        {/* Diagram card */}
        <div className="cdp-diagram-card">
          <div className="cdp-diagram-card-header">
            {/* Row 1: title + subtitle */}
            <div className="cdp-diagram-card-title">
              <Layers size={18} />
              <span>{diagram?.title || (isRTL ? 'مخطط الكلاسات' : 'Class Diagram')}</span>
              {diagram?.classes && (
                <span className="cdp-class-count">
                  {diagram.classes.length} {isRTL ? 'كلاس' : diagram.classes.length === 1 ? 'class' : 'classes'}
                </span>
              )}
            </div>
            <p className="cdp-diagram-subtitle">
              {isRTL ? 'مخطط تفاعلي — مُولَّد تلقائياً من الكود' : 'Interactive class diagram — auto-generated from source code'}
            </p>

            {/* Row 2: diagram toolbar (zoom + export) */}
            <div className="cdp-diagram-toolbar">
              {/* Zoom */}
              <div className="cdp-zoom-group">
                <button className="cdp-zoom-btn" onClick={() => setZoom(z => Math.max(0.3, z - 0.2))} title="Zoom out"><ZoomOut size={14} /></button>
                <span className="cdp-zoom-label">{Math.round(zoom * 100)}%</span>
                <button className="cdp-zoom-btn" onClick={() => setZoom(1)} title="Reset"><Maximize2 size={14} /></button>
                <button className="cdp-zoom-btn" onClick={() => setZoom(z => Math.min(3, z + 0.2))} title="Zoom in"><ZoomIn size={14} /></button>
              </div>

              {/* Divider */}
              <div className="cdp-toolbar-divider" />

              {/* Export PNG */}
              <button
                className="cdp-toolbar-btn"
                onClick={handleExportPNG}
                disabled={!isDiagramReady || isExporting}
                title="Export PNG"
              >
                {isExporting
                  ? <Loader size={13} className="cdp-spin" />
                  : <Download size={13} />
                }
                PNG
              </button>

              {/* Export SVG */}
              <button
                className="cdp-toolbar-btn"
                onClick={handleExportSVG}
                disabled={!isDiagramReady}
                title="Export SVG"
              >
                <Download size={13} />
                SVG
              </button>
            </div>
          </div>

          {diagramError && (
            <div className="cdp-error-banner" style={{ margin: '0 24px 16px' }}>
              <AlertCircle size={16} /><span>{diagramError}</span>
            </div>
          )}

          <div className="cdp-diagram-body">
            {diagram?.classes && diagram.classes.length > 0 ? (
              <div className="cdp-diagram-scroll">
                <div
                  ref={diagramRef}
                  className="cdp-diagram-inner"
                  style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.2s ease' }}
                  dangerouslySetInnerHTML={{ __html: mermaidSvg }}
                />
                {!isDiagramReady && !diagramError && (
                  <div className="cdp-diagram-loading">
                    <Loader size={28} className="cdp-spin" />
                    <p>{isRTL ? 'جاري توليد المخطط...' : 'Generating diagram...'}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="cdp-diagram-empty">
                <Layers size={56} style={{ opacity: 0.25 }} />
                <p>{isRTL ? 'لا توجد كلاسات' : 'No classes found'}</p>
                <span>{isRTL ? 'تأكد من أن الكود يحتوي على تعريفات كلاسات صحيحة' : 'Make sure your code contains valid class definitions'}</span>
              </div>
            )}
          </div>
        </div>

      </main>

      {/* ── Inline styles ───────────────────────────────────────────────────── */}
      <style>{`
        @keyframes cdp-spin { to { transform: rotate(360deg); } }
        .cdp-spin { animation: cdp-spin 0.9s linear infinite; }

        /* ── Dark mode diagram overrides ── */
        .cdp-page.dark .cdp-diagram-inner svg .classGroup rect,
        .cdp-page.dark .cdp-diagram-inner svg rect.classBox,
        .cdp-page.dark .cdp-diagram-inner svg g.classGroup > rect,
        .cdp-page.dark .cdp-diagram-inner svg .node rect {
          fill: #1a1a2e !important;
          stroke: #e879f9 !important;
          stroke-width: 2px !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .classGroup .label rect,
        .cdp-page.dark .cdp-diagram-inner svg .classGroup g rect:not(:first-child) {
          fill: transparent !important; stroke: none !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg text,
        .cdp-page.dark .cdp-diagram-inner svg tspan {
          fill: #e2d9f3 !important; color: #e2d9f3 !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .classTitle,
        .cdp-page.dark .cdp-diagram-inner svg text.classTitle {
          fill: #f0e6ff !important; font-weight: 700 !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .edgePath path {
          stroke: #e879f9 !important; stroke-width: 2.5px !important; fill: none !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg defs marker path,
        .cdp-page.dark .cdp-diagram-inner svg defs marker polygon,
        .cdp-page.dark .cdp-diagram-inner svg marker > path,
        .cdp-page.dark .cdp-diagram-inner svg marker > polygon {
          fill: #e879f9 !important; stroke: #e879f9 !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .classGroup line,
        .cdp-page.dark .cdp-diagram-inner svg line {
          stroke: #e879f9 !important; stroke-width: 1.5px !important; fill: none !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .edgeLabel rect {
          fill: #1a1a2e !important; stroke: rgba(232,121,249,0.35) !important;
        }
        .cdp-page.dark .cdp-diagram-inner svg .edgeLabel span,
        .cdp-page.dark .cdp-diagram-inner svg .edgeLabel p,
        .cdp-page.dark .cdp-diagram-inner svg foreignObject div {
          color: #e2d9f3 !important; background-color: rgba(26,26,46,0.90) !important;
        }

        /* ── Light mode diagram overrides ── */
        .cdp-page.light .cdp-diagram-inner svg .edgePath path {
          stroke: #4c1d95 !important; stroke-width: 2px !important; fill: none !important;
        }
        .cdp-page.light .cdp-diagram-inner svg defs marker path,
        .cdp-page.light .cdp-diagram-inner svg defs marker polygon {
          fill: #4c1d95 !important; stroke: #4c1d95 !important;
        }
        .cdp-page.light .cdp-diagram-inner svg .classGroup line,
        .cdp-page.light .cdp-diagram-inner svg line {
          stroke: #4c1d95 !important;
        }
      `}</style>

    </div>
  );
};

export default ClassDiagramPage;
