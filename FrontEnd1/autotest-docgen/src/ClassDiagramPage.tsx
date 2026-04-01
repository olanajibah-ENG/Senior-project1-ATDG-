import React, { useRef, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, Layers, AlertCircle, Zap, FileText,
  Loader, CheckCircle, Sun, Moon, ZoomIn, ZoomOut, Maximize2
} from 'lucide-react';
import UnifiedApiService from './services/unifiedApiService';
import './DocumentGenerationPage.css';

interface DiagramAttribute {
  name: string;
  type: string;
  visibility: 'public' | 'private' | 'protected' | 'package';
}

interface MethodParameter {
  name: string;
  type: string;
}

interface DiagramMethod {
  name: string;
  parameters: MethodParameter[];
  return_type: string;
  visibility: 'public' | 'private' | 'protected' | 'package';
  type: 'constructor' | 'method';
}

interface DiagramClass {
  name: string;
  attributes?: DiagramAttribute[];
  methods?: DiagramMethod[];
  is_abstract?: boolean;
  is_interface?: boolean;
}

interface ClassRelationship {
  from: string;
  to: string;
  type: 'inheritance' | 'implementation' | 'composition' | 'aggregation' | 'association' | 'dependency';
  label?: string;
}

interface DiagramLocationState {
  projectId: string;
  codeName: string;
  fileName: string;
  isProjectDiagram?: boolean;
  analysisIds?: string[];
  diagram: {
    title?: string;
    classes?: DiagramClass[];
    relationships?: ClassRelationship[];
  };
}

const ClassDiagramPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const diagramRef = useRef<HTMLDivElement>(null);

  const [mermaidSvg, setMermaidSvg] = useState<string>('');
  const [isDiagramReady, setIsDiagramReady] = useState(false);
  const [diagramError, setDiagramError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Close export menu when clicking outside
  useEffect(() => {
    if (!showExportMenu) return;
    const close = () => setShowExportMenu(false);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [showExportMenu]);

  // Explanation states
  const [explanationType, setExplanationType] = useState<'high_level' | 'low_level'>('high_level');
  const [isGeneratingExplanation, setIsGeneratingExplanation] = useState(false);
  const [explanationDone, setExplanationDone] = useState(false);
  const [explanationAnalysisId, setExplanationAnalysisId] = useState<string | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  // Export/Document states
  const [isExportingDocument, setIsExportingDocument] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'md'>('pdf');

  const state = (location.state || {}) as DiagramLocationState;
  const { codeName, diagram, isProjectDiagram, analysisIds } = state;

  // Sync dark mode with body
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  const getVisibilitySymbol = (v: string) =>
    ({ public: '+', private: '-', protected: '#', package: '~' }[v] ?? '+');

  const cleanType = (t: string) =>
    t.replace(/</g, '~').replace(/>/g, '~').replace(/[^a-zA-Z0-9_~\[\]]/g, '_');

  const buildMermaidCode = (): string => {
    if (!diagram?.classes?.length) return '';
    const knownClasses = new Set(
      (diagram.classes || []).map(c => c.name.replace(/[^a-zA-Z0-9_]/g, '_'))
    );

    let code = 'classDiagram\n';

    diagram.classes.forEach(cls => {
      const name = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
      code += `    class ${name} {\n`;
      if (cls.is_interface) code += `        <<interface>>\n`;
      else if (cls.is_abstract) code += `        <<abstract>>\n`;

      (cls.attributes || []).forEach(attr => {
        code += `        ${getVisibilitySymbol(attr.visibility)}${cleanType(attr.type)} ${attr.name}\n`;
      });
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
      if (!knownClasses.has(to)) return;
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

  useEffect(() => {
    if (!diagram?.classes?.length) return;

    const generate = async () => {
      try {
        const mermaid = (await import('mermaid')).default;

        // ألوان مختلفة حسب الـ dark/light mode
        const darkVars = {
          primaryColor: '#4a2080',
          primaryTextColor: '#f0e6ff',
          primaryBorderColor: '#e879f9',
          lineColor: '#e879f9',
          secondaryColor: '#2d1b4e',
          tertiaryColor: '#1a1035',
          edgeLabelBackground: '#4a2080',
          titleColor: '#ffffff',
          attributeBackgroundColorEven: '#3b1a6e',
          attributeBackgroundColorOdd: '#4a2080',
          classText: '#f0e6ff',
          nodeBorder: '#e879f9',
          mainBkg: '#4a2080',
          nodeBkg: '#4a2080',
          clusterBkg: '#1a1035',
          defaultLinkColor: '#e879f9',
          fontFamily: 'Inter, sans-serif',
          fontSize: '14px',
          labelBackground: '#4a2080',
          labelTextColor: '#f0e6ff',
          background: '#0f0a1e',
          textColor: '#f0e6ff',
        };

        const lightVars = {
          primaryColor: '#f3e8ff',
          primaryTextColor: '#1a202c',
          primaryBorderColor: '#805ad5',
          lineColor: '#4c1d95',
          secondaryColor: '#e9d8fd',
          tertiaryColor: '#faf5ff',
          edgeLabelBackground: '#f3e8ff',
          titleColor: '#4c1d95',
          classText: '#1a202c',
          nodeBorder: '#805ad5',
          mainBkg: '#f3e8ff',
          nodeBkg: '#f3e8ff',
        };

        mermaid.initialize({
          startOnLoad: false,
          theme: 'base',
          securityLevel: 'loose',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          themeVariables: isDarkMode ? darkVars : lightVars,
        } as any);

        const code = buildMermaidCode();
        console.log('Mermaid:\n', code);
        const { svg } = await mermaid.render(`diagram-${Date.now()}`, code);
        setMermaidSvg(svg);
        setIsDiagramReady(true);
        setDiagramError(null);
      } catch (e: any) {
        console.error('Mermaid error:', e);
        setDiagramError(e?.message || 'Failed to render diagram');
        setIsDiagramReady(false);
      }
    };

    generate();
  }, [diagram, isDarkMode]);

  // ===== Generate Explanation =====
  const handleGenerateExplanation = async () => {
    if (isGeneratingExplanation) return;
    const targetId = analysisIds?.[0] || state.projectId;
    if (!targetId) { setExplanationError('No analysis ID available.'); return; }

    setIsGeneratingExplanation(true);
    setExplanationError(null);
    setExplanationDone(false);

    try {
      const result = await UnifiedApiService.generateExplanation(targetId, explanationType);
      const taskId = result.task_id;
      const expId = result.analysis_id || targetId;

      if (taskId) {
        for (let i = 1; i <= 30; i++) {
          await new Promise(r => setTimeout(r, 3000));
          try {
            const s = await UnifiedApiService.getExplanationTaskStatus(taskId);
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

  // ===== Export Document =====
  const handleExportDocument = async () => {
    if (!explanationDone || !explanationAnalysisId || isExportingDocument) return;
    setIsExportingDocument(true);
    try {
      const blob = await UnifiedApiService.exportDocument(explanationAnalysisId, {
        format: exportFormat, type: explanationType, mode: 'download',
      });
      if (blob.size === 0) throw new Error('Downloaded file is empty');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${codeName || 'project'}_explanation.${exportFormat === 'pdf' ? 'pdf' : 'md'}`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setIsExportingDocument(false);
    }
  };

  // ===== Export SVG =====
  const handleExportSVG = () => {
    if (!diagramRef.current || !isDiagramReady) return;
    const svgEl = diagramRef.current.querySelector('svg');
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const a = document.createElement('a');
    a.download = `${(codeName || 'diagram').replace(/\s+/g, '_')}_class_diagram.svg`;
    a.href = URL.createObjectURL(blob);
    a.click();
    URL.revokeObjectURL(a.href);
  };

  // ===== Export PNG =====
  const handleExportPNG = async () => {
      if (!diagramRef.current || !isDiagramReady) return;
      setIsExporting(true);
      try {
        const svgEl = diagramRef.current.querySelector('svg');
        if (!svgEl) throw new Error('SVG not found');

        // Get real dimensions from viewBox
        const vb = svgEl.getAttribute('viewBox')?.split(' ').map(Number) || [];
        const svgW = vb[2] || svgEl.clientWidth || 1200;
        const svgH = vb[3] || svgEl.clientHeight || 900;

        const clone = svgEl.cloneNode(true) as SVGElement;
        clone.setAttribute('width', String(svgW));
        clone.setAttribute('height', String(svgH));
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

        // Replace foreignObject (HTML) with SVG text — canvas can't render foreignObject
        clone.querySelectorAll('foreignObject').forEach(fo => {
          const parent = fo.parentNode;
          if (!parent) return;

          // Get position from parent transform
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
          textEl.setAttribute('fill', isDarkMode ? '#f0e6ff' : '#1a202c');
          textEl.setAttribute('font-family', 'Arial, sans-serif');
          textEl.setAttribute('font-size', '13');
          textEl.textContent = text;
          parent.replaceChild(textEl, fo);
        });

        // Apply colors
        if (isDarkMode) {
          clone.querySelectorAll('rect').forEach(r => {
            if (r.getAttribute('width') === '100%') { r.setAttribute('fill', '#0f0a1e'); return; }
            if (r.getAttribute('stroke-width') === '0') { r.setAttribute('fill', '#4a2080'); r.setAttribute('stroke', 'none'); return; }
            r.setAttribute('fill', '#4a2080');
            r.setAttribute('stroke', '#e879f9');
          });
          clone.querySelectorAll('text, tspan').forEach(t => t.setAttribute('fill', '#f0e6ff'));
          clone.querySelectorAll('.edgePath path, .relation').forEach(p => {
            p.setAttribute('stroke', '#e879f9'); p.setAttribute('stroke-width', '2.5');
          });
          clone.querySelectorAll('marker path, marker polygon').forEach(m => {
            m.setAttribute('fill', '#e879f9'); m.setAttribute('stroke', '#e879f9');
          });
          clone.querySelectorAll('line').forEach(l => l.setAttribute('stroke', '#e879f9'));
        }

        const svgStr = new XMLSerializer().serializeToString(clone);
        const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const scale = 2;
        const canvas = document.createElement('canvas');
        canvas.width = svgW * scale;
        canvas.height = svgH * scale;
        const ctx = canvas.getContext('2d')!;
        ctx.fillStyle = isDarkMode ? '#0f0a1e' : '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.scale(scale, scale);

        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, 0, 0, svgW, svgH);
          URL.revokeObjectURL(url);
          canvas.toBlob(pngBlob => {
            if (pngBlob) {
              const a = document.createElement('a');
              a.download = `${(codeName || 'diagram').replace(/\s+/g, '_')}_class_diagram.png`;
              a.href = URL.createObjectURL(pngBlob);
              document.body.appendChild(a);
              a.click();
              setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 200);
            }
            setIsExporting(false);
          }, 'image/png', 1.0);
        };
        img.onerror = (e) => { console.error('img load error', e); URL.revokeObjectURL(url); setIsExporting(false); };
        img.src = url;
      } catch (e) {
        console.error('PNG export error:', e);
        setIsExporting(false);
      }
    };

  return (
    <div className={`premium-hero ${isDarkMode ? 'dark' : 'light'}`}>

      {/* Animated Background */}
      <div className="animated-bg">
        <div className="floating-particles">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="particle" style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 10}s`,
              animationDuration: `${15 + Math.random() * 10}s`
            }} />
          ))}
        </div>
      </div>

      {/* Header */}
      <div className="doc-gen-header">
        <div className="header-left">
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            <ArrowLeft size={18} /> Back
          </button>
        </div>

        <h1 className="doc-gen-title">
          <Layers size={24} />
          {codeName || 'Class Diagram'}
          {isProjectDiagram && (
            <span className="status-badge auto-generated" style={{ fontSize: '0.75rem' }}>
              <span className="badge-dot" /> Project
            </span>
          )}
        </h1>

        <div className="header-right">
          <button className="toggle-btn" onClick={() => setIsDarkMode(!isDarkMode)}
            title={isDarkMode ? 'Light Mode' : 'Dark Mode'}>
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>

      {/* Controls Bar */}
      <div style={{
        margin: '88px 24px 24px 24px',
        padding: '20px 24px',
        background: isDarkMode ? 'rgba(26,16,53,0.95)' : 'rgba(255,255,255,0.95)',
        border: `1px solid ${isDarkMode ? 'rgba(118,75,162,0.35)' : 'rgba(0,0,0,0.1)'}`,
        borderRadius: '14px',
        backdropFilter: 'blur(12px)',
        boxShadow: isDarkMode ? '0 8px 32px rgba(0,0,0,0.4)' : '0 8px 32px rgba(0,0,0,0.1)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '24px',
        alignItems: 'flex-end',
      }}>

        {/* Export — toggle PNG / SVG مثل High/Low */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <label style={{
            fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.6px', color: isDarkMode ? '#a78bca' : '#6b7280',
            display: 'flex', alignItems: 'center', gap: '6px'
          }}>
            <Download size={14} /> Export Diagram
          </label>
          <div style={{
            display: 'flex', borderRadius: '10px', overflow: 'hidden',
            border: `2px solid ${isDarkMode ? 'rgba(118,75,162,0.50)' : 'rgba(79,70,229,0.25)'}`,
            background: isDarkMode ? 'rgba(40,22,75,0.80)' : 'rgba(255,255,255,0.8)',
          }}>
            <button
              onClick={handleExportPNG}
              disabled={!isDiagramReady || isExporting}
              style={{
                padding: '11px 22px', border: 'none', fontWeight: 700,
                fontSize: '14px', cursor: isDiagramReady && !isExporting ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s ease', whiteSpace: 'nowrap',
                background: 'transparent',
                color: isDarkMode ? '#a78bca' : '#6b7280',
                opacity: !isDiagramReady ? 0.5 : 1,
                display: 'flex', alignItems: 'center', gap: '6px',
              }}>
              <Download size={14} />
              {isExporting ? 'Exporting...' : 'PNG'}
            </button>
            <button
              onClick={handleExportSVG}
              disabled={!isDiagramReady}
              style={{
                padding: '11px 22px', border: 'none', fontWeight: 700,
                fontSize: '14px', cursor: isDiagramReady ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s ease', whiteSpace: 'nowrap',
                background: 'transparent',
                color: isDarkMode ? '#a78bca' : '#6b7280',
                opacity: !isDiagramReady ? 0.5 : 1,
                display: 'flex', alignItems: 'center', gap: '6px',
                borderLeft: `1px solid ${isDarkMode ? 'rgba(118,75,162,0.40)' : 'rgba(79,70,229,0.20)'}`,
              }}>
              <Download size={14} />
              SVG
            </button>
          </div>
        </div>

        {/* Explanation Level + Generate — project diagrams only */}
        {isProjectDiagram && (
          <>
            {/* Toggle: High / Low */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{
                fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.6px', color: isDarkMode ? '#a78bca' : '#6b7280',
                display: 'flex', alignItems: 'center', gap: '6px'
              }}>
                <Zap size={14} /> Explanation Level
              </label>
              <div style={{
                display: 'flex', borderRadius: '10px', overflow: 'hidden',
                border: `2px solid ${isDarkMode ? 'rgba(118,75,162,0.50)' : 'rgba(79,70,229,0.25)'}`,
                background: isDarkMode ? 'rgba(40,22,75,0.80)' : 'rgba(255,255,255,0.8)',
              }}>
                {(['high_level', 'low_level'] as const).map(val => (
                  <button key={val}
                    onClick={() => setExplanationType(val)}
                    disabled={isGeneratingExplanation || explanationDone}
                    style={{
                      padding: '11px 22px', border: 'none', fontWeight: 700,
                      fontSize: '14px', cursor: isGeneratingExplanation || explanationDone ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s ease', whiteSpace: 'nowrap',
                      background: explanationType === val
                        ? 'linear-gradient(135deg,#667eea,#764ba2)'
                        : 'transparent',
                      color: explanationType === val
                        ? '#fff'
                        : isDarkMode ? '#a78bca' : '#6b7280',
                    }}>
                    {val === 'high_level' ? 'High Level' : 'Low Level'}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Explanations button */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{
                fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.6px', color: isDarkMode ? '#a78bca' : '#6b7280',
                display: 'flex', alignItems: 'center', gap: '6px'
              }}>
                <Zap size={14} /> Generate
              </label>
              <button onClick={handleGenerateExplanation}
                disabled={isGeneratingExplanation || explanationDone}
                style={{
                  background: explanationDone
                    ? 'linear-gradient(135deg,#10b981,#059669)'
                    : isGeneratingExplanation
                      ? 'rgba(118,75,162,0.40)'
                      : 'linear-gradient(135deg,#667eea,#764ba2)',
                  color: '#fff', border: 'none', borderRadius: '10px',
                  padding: '11px 20px', fontWeight: 700, fontSize: '14px',
                  cursor: isGeneratingExplanation || explanationDone ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: '8px',
                  boxShadow: '0 4px 12px rgba(118,75,162,0.35)',
                  whiteSpace: 'nowrap',
                }}>
                {isGeneratingExplanation
                  ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Generating...</>
                  : explanationDone
                    ? <><CheckCircle size={15} /> Explanation Ready</>
                    : <><Zap size={15} /> Generate Explanations</>}
              </button>
            </div>
          </>
        )}

        {/* Format + Download Document — after explanation done */}
        {isProjectDiagram && explanationDone && (
          <>
            {/* Toggle: PDF / Markdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{
                fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.6px', color: isDarkMode ? '#a78bca' : '#6b7280',
                display: 'flex', alignItems: 'center', gap: '6px'
              }}>
                <FileText size={14} /> Document Format
              </label>
              <div style={{
                display: 'flex', borderRadius: '10px', overflow: 'hidden',
                border: `2px solid ${isDarkMode ? 'rgba(118,75,162,0.50)' : 'rgba(79,70,229,0.25)'}`,
                background: isDarkMode ? 'rgba(40,22,75,0.80)' : 'rgba(255,255,255,0.8)',
              }}>
                {(['pdf', 'md'] as const).map(val => (
                  <button key={val}
                    onClick={() => setExportFormat(val)}
                    disabled={isExportingDocument}
                    style={{
                      padding: '11px 22px', border: 'none', fontWeight: 700,
                      fontSize: '14px', cursor: isExportingDocument ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s ease', whiteSpace: 'nowrap',
                      background: exportFormat === val
                        ? 'linear-gradient(135deg,#667eea,#764ba2)'
                        : 'transparent',
                      color: exportFormat === val
                        ? '#fff'
                        : isDarkMode ? '#a78bca' : '#6b7280',
                    }}>
                    {val === 'pdf' ? 'PDF' : 'Markdown'}
                  </button>
                ))}
              </div>
            </div>

            {/* Download Document button */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{
                fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.6px', color: isDarkMode ? '#a78bca' : '#6b7280',
                display: 'flex', alignItems: 'center', gap: '6px'
              }}>
                <FileText size={14} /> Download
              </label>
              <button onClick={handleExportDocument} disabled={isExportingDocument} style={{
                background: isExportingDocument
                  ? 'rgba(118,75,162,0.40)'
                  : 'linear-gradient(135deg,#f093fb,#764ba2)',
                color: '#fff', border: 'none', borderRadius: '10px',
                padding: '11px 20px', fontWeight: 700, fontSize: '14px',
                cursor: isExportingDocument ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: '8px',
                boxShadow: '0 4px 12px rgba(240,147,251,0.35)',
                whiteSpace: 'nowrap',
              }}>
                {isExportingDocument
                  ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Downloading...</>
                  : <><FileText size={15} /> Generate Document</>}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Main Content */}
      <div className="doc-gen-content" style={{ paddingTop: '8px' }}>

        {/* Explanation error */}
        {explanationError && (
          <div style={{
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '12px', padding: '12px 20px', display: 'flex',
            alignItems: 'center', gap: '10px', color: '#fca5a5'
          }}>
            <AlertCircle size={18} /><span>{explanationError}</span>
          </div>
        )}

        {/* Diagram Section */}
        <div className={`content-section diagram-section ${isDarkMode ? 'bg-black/20 border-white/10' : 'bg-white/70 border-gray-200/50'}`}>
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">
                <div className="title-icon"><Layers size={22} /></div>
                <span className="title-text" style={{ color: isDarkMode ? '#f3e8ff' : '#1e293b' }}>
                  {diagram?.title || 'System Architecture'}
                </span>
                {diagram?.classes && (
                  <div className="status-badge auto-generated">
                    <span className="badge-dot" />
                    {diagram.classes.length} {diagram.classes.length === 1 ? 'Class' : 'Classes'}
                  </div>
                )}
              </h2>
              <p className="section-description" style={{
                color: isDarkMode ? '#c084fc' : '#6b7280',
                paddingLeft: '0',
              }}>
                Interactive class diagram — auto-generated from source code
              </p>
            </div>

            {/* Zoom controls */}
            <div className="section-actions">
              <div className="diagram-zoom-controls">
                <button className="btn-zoom" onClick={() => setZoom(z => Math.max(0.5, z - 0.2))}><ZoomOut size={16} /></button>
                <button className="btn-zoom" onClick={() => setZoom(1)}><Maximize2 size={16} /></button>
                <button className="btn-zoom" onClick={() => setZoom(z => Math.min(3, z + 0.2))}><ZoomIn size={16} /></button>
              </div>
            </div>
          </div>

          {diagramError && (
            <div style={{
              margin: '16px 32px', background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px',
              padding: '12px 16px', display: 'flex', alignItems: 'center',
              gap: '12px', color: '#fca5a5'
            }}>
              <AlertCircle size={20} /><span>{diagramError}</span>
            </div>
          )}

          <div className="diagram-container" style={{ padding: '24px' }}>
            {diagram?.classes && diagram.classes.length > 0 ? (
              <div className="diagram-wrapper" style={{
                maxHeight: '700px', overflow: 'auto',
                background: isDarkMode
                  ? 'linear-gradient(135deg, #0f0a1e 0%, #1a1035 100%)'
                  : '#f8fafc',
                border: `2px solid ${isDarkMode ? 'rgba(192,132,252,0.35)' : 'rgba(128,90,213,0.25)'}`,
              }}>
                <div
                  ref={diagramRef}
                  className="diagram-content"
                  style={{
                    transform: `scale(${zoom})`,
                    transformOrigin: 'top center',
                    transition: 'transform 0.2s ease',
                    padding: '60px 20px 20px',
                  }}
                  dangerouslySetInnerHTML={{ __html: mermaidSvg }}
                />
                {!isDiagramReady && !diagramError && (
                  <div className="loading-state">
                    <div className="spinner" />
                    <p className="loading-text">Generating diagram...</p>
                    <p className="loading-subtext">Building class structure visualization</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="diagram-empty">
                <Layers size={64} style={{ opacity: 0.3 }} />
                <p style={{ fontSize: '1.1rem', fontWeight: 600 }}>No classes found</p>
                <p style={{ fontSize: '0.9rem', opacity: 0.7 }}>
                  Make sure your code contains valid class definitions.
                </p>
              </div>
            )}
          </div>
        </div>

      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Dark: class box fill ── */
        .premium-hero.dark .diagram-content svg .classGroup rect,
        .premium-hero.dark .diagram-content svg rect.classBox,
        .premium-hero.dark .diagram-content svg g.classGroup > rect,
        .premium-hero.dark .diagram-content svg .node rect {
          fill: #4a2080 !important;
          stroke: #e879f9 !important;
          stroke-width: 2px !important;
        }
        /* خلفية rows داخل الـ class شفافة */
        .premium-hero.dark .diagram-content svg .classGroup .label rect,
        .premium-hero.dark .diagram-content svg .classGroup g rect:not(:first-child) {
          fill: transparent !important;
          stroke: none !important;
        }

        /* ── Dark: ALL text — فاتح واضح ── */
        .premium-hero.dark .diagram-content svg text,
        .premium-hero.dark .diagram-content svg tspan,
        .premium-hero.dark .diagram-content svg text[style],
        .premium-hero.dark .diagram-content svg tspan[style] {
          fill: #f0e6ff !important;
          color: #f0e6ff !important;
        }
        /* override mermaid's g.classGroup text { fill:#e879f9 } */
        .premium-hero.dark .diagram-content svg g.classGroup text,
        .premium-hero.dark .diagram-content svg g.classGroup tspan,
        .premium-hero.dark .diagram-content svg .nodeLabel,
        .premium-hero.dark .diagram-content svg .nodeLabel p,
        .premium-hero.dark .diagram-content svg .nodeLabel span {
          fill: #f0e6ff !important;
          color: #f0e6ff !important;
        }
        /* class name (title) أبيض */
        .premium-hero.dark .diagram-content svg .classTitle,
        .premium-hero.dark .diagram-content svg text.classTitle,
        .premium-hero.dark .diagram-content svg .classTitleText {
          fill: #ffffff !important;
          font-weight: 700 !important;
        }
        /* ── Dark: relationship arrows ── */
        .premium-hero.dark .diagram-content svg .edgePath path {
          stroke: #e879f9 !important;
          stroke-width: 2.5px !important;
          fill: none !important;
        }
        .premium-hero.dark .diagram-content svg defs marker path,
        .premium-hero.dark .diagram-content svg defs marker polygon,
        .premium-hero.dark .diagram-content svg marker > path,
        .premium-hero.dark .diagram-content svg marker > polygon {
          fill: #e879f9 !important;
          stroke: #e879f9 !important;
        }

        /* ── Dark: divider lines ── */
        .premium-hero.dark .diagram-content svg .classGroup line,
        .premium-hero.dark .diagram-content svg line {
          stroke: #e879f9 !important;
          stroke-width: 1.5px !important;
          fill: none !important;
        }

        /* ── Dark: edge label ── */
        .premium-hero.dark .diagram-content svg .edgeLabel rect {
          fill: #4a2080 !important;
          stroke: rgba(232,121,249,0.35) !important;
        }
        .premium-hero.dark .diagram-content svg .edgeLabel span,
        .premium-hero.dark .diagram-content svg .edgeLabel p,
        .premium-hero.dark .diagram-content svg foreignObject div {
          color: #e2d9f3 !important;
          background-color: rgba(74,32,128,0.90) !important;
        }

        /* ── Light: arrows ── */
        .premium-hero.light .diagram-content svg .edgePath path {
          stroke: #4c1d95 !important;
          stroke-width: 2px !important;
          fill: none !important;
        }
        .premium-hero.light .diagram-content svg defs marker path,
        .premium-hero.light .diagram-content svg defs marker polygon {
          fill: #4c1d95 !important;
          stroke: #4c1d95 !important;
        }
      `}</style>
    </div>
  );
};

export default ClassDiagramPage;
