import React, { useRef, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Code, Layers, AlertCircle } from 'lucide-react';
import './styles/diagram.css';

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
  diagram: {
    title?: string;
    description?: string;
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

  const state = (location.state || {}) as DiagramLocationState;
  const { codeName, fileName, diagram } = state;

  // تحويل رموز الـ visibility
  const getVisibilitySymbol = (visibility: string): string => {
    switch (visibility) {
      case 'public': return '+';
      case 'private': return '-';
      case 'protected': return '#';
      case 'package': return '~';
      default: return '+';
    }
  };

  // تنسيق المعاملات
  const formatParameters = (parameters: MethodParameter[]): string => {
    if (!parameters || parameters.length === 0) return '';
    return parameters
      .map(p => `${p.name}: ${p.type.replace(/</g, '&lt;').replace(/>/g, '&gt;')}`)
      .join(', ');
  };

  // تحويل العلاقات إلى Mermaid syntax
  const getRelationshipSyntax = (rel: ClassRelationship): string => {
    const fromName = rel.from.replace(/[^a-zA-Z0-9_]/g, '_');
    const toName = rel.to.replace(/[^a-zA-Z0-9_]/g, '_');
    const label = rel.label ? ` : ${rel.label}` : '';

    switch (rel.type) {
      case 'inheritance':
        return `${fromName} --|> ${toName}${label}`;
      case 'implementation':
        return `${fromName} ..|> ${toName}${label}`;
      case 'composition':
        return `${fromName} *-- ${toName}${label}`;
      case 'aggregation':
        return `${fromName} o-- ${toName}${label}`;
      case 'association':
        return `${fromName} --> ${toName}${label}`;
      case 'dependency':
        return `${fromName} ..> ${toName}${label}`;
      default:
        return `${fromName} --> ${toName}${label}`;
    }
  };

  useEffect(() => {
    const generateDiagram = async () => {
      try {
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'base',
          securityLevel: 'loose',
          fontFamily: 'ui-monospace, Monaco, "Cascadia Mono", "Segoe UI Mono", Consolas, monospace',
          themeVariables: {
            primaryColor: '#d6bcfa',
            primaryTextColor: '#000000',
            primaryBorderColor: '#805ad5',
            lineColor: '#000000',
            secondaryColor: '#d6bcfa',
            tertiaryColor: '#faf5ff',
            noteBkgColor: '#e9d8fd',
            noteTextColor: '#1a202c'
          }
        } as any);

        let mermaidCode = 'classDiagram\n';

        if (diagram && diagram.classes) {
          diagram.classes.forEach(cls => {
            const className = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');

            // ✅ إضافة الكلاس أولاً (سطر منفصل)
            mermaidCode += `    class ${className}\n`;

            // ✅ ثم إضافة المعدلات على سطر منفصل
            if (cls.is_abstract) {
              mermaidCode += `    <<abstract>> ${className}\n`;
            } else if (cls.is_interface) {
              mermaidCode += `    <<interface>> ${className}\n`;
            }

            // إضافة الخصائص
            if (cls.attributes && cls.attributes.length > 0) {
              cls.attributes.forEach(attr => {
                const symbol = getVisibilitySymbol(attr.visibility);
                mermaidCode += `    ${className} : ${symbol}${attr.type.replace(/</g, '&lt;').replace(/>/g, '&gt;')} ${attr.name}\n`;
              });
            }

            // إضافة الطرق
            if (cls.methods && cls.methods.length > 0) {
              cls.methods.forEach(method => {
                const symbol = getVisibilitySymbol(method.visibility);
                const params = formatParameters(method.parameters);
                const returnType = method.return_type !== 'void' ? ` ${method.return_type.replace(/</g, '&lt;').replace(/>/g, '&gt;')}` : '';
                mermaidCode += `    ${className} : ${symbol}${method.name}(${params})${returnType}\n`;
              });
            }
          });

          // إضافة العلاقات
          if (diagram.relationships && diagram.relationships.length > 0) {
            mermaidCode += '\n';
            diagram.relationships.forEach(rel => {
              mermaidCode += `    ${getRelationshipSyntax(rel)}\n`;
            });
          }
        }

        console.log('Generated Mermaid Code:', mermaidCode);

        const { svg } = await mermaid.render(`diagram-${Date.now()}`, mermaidCode);
        setMermaidSvg(svg);
        setIsDiagramReady(true);
        setDiagramError(null);
      } catch (error) {
        console.error('Diagram generation error:', error);
        setDiagramError('Failed to generate class diagram. Please check the code structure.');
        setIsDiagramReady(false);
      }
    };

    if (diagram && diagram.classes && diagram.classes.length > 0) {
      generateDiagram();
    }
  }, [diagram]);

  // تصدير الصورة بجودة عالية
  const handleExportPNG = async () => {
    if (!diagramRef.current || !isDiagramReady) return;

    setIsExporting(true);
    try {
      const svgElement = diagramRef.current.querySelector('svg');
      if (!svgElement) {
        throw new Error('SVG element not found');
      }

      // الحصول على أبعاد SVG
      const bbox = svgElement.getBBox();
      const padding = 40;
      const width = bbox.width + (padding * 2);
      const height = bbox.height + (padding * 2);

      // إنشاء canvas بجودة عالية
      const scale = 3; // 3x resolution للجودة العالية
      const canvas = document.createElement('canvas');
      canvas.width = width * scale;
      canvas.height = height * scale;
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        throw new Error('Canvas context not available');
      }

      // خلفية بيضاء
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // تحويل SVG إلى صورة
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      const img = new Image();
      img.onload = () => {
        ctx.scale(scale, scale);
        ctx.drawImage(img, padding, padding);

        // تنزيل الصورة
        canvas.toBlob((blob) => {
          if (blob) {
            const link = document.createElement('a');
            link.download = `${codeName.replace(/\s+/g, '_')}_class_diagram.png`;
            link.href = URL.createObjectURL(blob);
            link.click();

            URL.revokeObjectURL(url);
            URL.revokeObjectURL(link.href);
          }
          setIsExporting(false);
        }, 'image/png', 1.0);
      };

      img.onerror = () => {
        setIsExporting(false);
        alert('Failed to export diagram. Please try again.');
        URL.revokeObjectURL(url);
      };

      img.src = url;
    } catch (error) {
      console.error('Export error:', error);
      setIsExporting(false);
      alert('Failed to export diagram. Please try again.');
    }
  };

  return (
    <div className="dashboard-layout" style={{
      padding: '40px',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      minHeight: '100vh',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      {/* Header Section */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '30px',
        background: 'rgba(255, 255, 255, 0.9)',
        padding: '20px 30px',
        borderRadius: '16px',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}>
        <button
          onClick={() => navigate('/dashboard')}
          className="btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            color: '#4a5568',
            fontWeight: 600,
            fontSize: '15px',
            padding: '8px 12px',
            borderRadius: '8px',
            transition: 'all 0.2s ease'
          }}
        >
          <ArrowLeft size={20} /> Back to Dashboard
        </button>

        <div style={{ textAlign: 'center' }}>
          <h2 style={{
            margin: 0,
            fontSize: '1.5rem',
            color: '#2d3748',
            fontWeight: 700
          }}>
            Class Diagram Visualizer
          </h2>
          <span style={{ fontSize: '0.9rem', color: '#718096' }}>
            {codeName} {fileName && `• ${fileName}`}
          </span>
        </div>

        <button
          onClick={handleExportPNG}
          disabled={!isDiagramReady || isExporting}
          style={{
            backgroundColor: isDiagramReady && !isExporting ? '#4C51BF' : '#cbd5e0',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            border: 'none',
            cursor: isDiagramReady && !isExporting ? 'pointer' : 'not-allowed',
            transition: 'all 0.3s ease',
            fontSize: '14px',
            fontWeight: 600,
            boxShadow: isDiagramReady && !isExporting ? '0 4px 12px rgba(76, 81, 191, 0.3)' : 'none',
            transform: 'translateY(0)'
          }}
        >
          <Download size={18} />
          {isExporting ? 'Exporting...' : 'Export PNG'}
        </button>
      </div>

      {/* Main Content Card */}
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        minHeight: '700px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '30px',
          paddingBottom: '20px',
          borderBottom: '2px solid #edf2f7'
        }}>
          <Layers size={28} style={{ color: '#4C51BF' }} />
          <h3 style={{
            margin: 0,
            fontSize: '1.35rem',
            color: '#2d3748',
            fontWeight: 700
          }}>
            {diagram?.title || 'System Architecture'}
          </h3>
          {diagram?.classes && (
            <span style={{
              marginLeft: 'auto',
              background: '#eef2ff',
              color: '#4C51BF',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}>
              {diagram.classes.length} {diagram.classes.length === 1 ? 'Class' : 'Classes'}
            </span>
          )}
        </div>

        {diagramError && (
          <div style={{
            background: '#fff5f5',
            border: '1px solid #fc8181',
            borderRadius: '12px',
            padding: '16px 20px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            color: '#c53030'
          }}>
            <AlertCircle size={20} />
            <span>{diagramError}</span>
          </div>
        )}

        {diagram?.classes && diagram.classes.length > 0 ? (
          <div ref={diagramRef} style={{ position: 'relative' }}>
            <div style={{
              background: '#fafbfc',
              border: '2px solid #e2e8f0',
              borderRadius: '16px',
              padding: '15px',
              overflow: 'auto',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '300px',
              boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.04)'
            }}>
              <div
                className={`mermaid-wrapper ${isDiagramReady ? 'visible' : 'loading'}`}
                style={{
                  transition: 'all 0.5s ease',
                  transform: isDiagramReady ? 'scale(1)' : 'scale(0.95)',
                  opacity: isDiagramReady ? 1 : 0.3
                }}
                dangerouslySetInnerHTML={{ __html: mermaidSvg }}
              />

              {!isDiagramReady && !diagramError && (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  color: '#718096'
                }}>
                  <div className="spinner" style={{
                    width: '40px',
                    height: '40px',
                    border: '4px solid #e2e8f0',
                    borderTop: '4px solid #4C51BF',
                    borderRadius: '50%',
                    margin: '0 auto 12px'
                  }} />
                  <p>Generating diagram...</p>
                </div>
              )}
            </div>

            {/* Legend */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              right: '20px',
              background: 'rgba(255,255,255,0.95)',
              padding: '10px 16px',
              borderRadius: '10px',
              fontSize: '0.8rem',
              border: '1px solid #e2e8f0',
              color: '#64748b',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Code size={16} />
              Auto-generated from Source Code
            </div>
          </div>
        ) : (
          <div className="empty-state" style={{
            textAlign: 'center',
            padding: '80px 20px',
            color: '#718096'
          }}>
            <Layers size={64} style={{ opacity: 0.3, margin: '0 auto 20px' }} />
            <p style={{ fontSize: '1.1rem', margin: 0, fontWeight: 600 }}>
              No architecture patterns found in this file.
            </p>
            <p style={{ fontSize: '0.9rem', marginTop: '8px', opacity: 0.8 }}>
              Make sure your code contains class definitions with proper structure.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassDiagramPage;