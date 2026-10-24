import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Code, Calendar, FileText, Download, RefreshCw } from 'lucide-react';
import apiService, { type ProjectCode } from './services/api.service';
import apiClient from './services/apiClient';
import './ProjectFilesPage.css';   // نعيد استخدام أسلوب الـtopbar/back-btn الموحّد بين صفحات المشروع
import './ProjectCodesPage.css';   // أنماط خاصة بقائمة الأكواد

// ─────────────────────────────────────────────────────────────────────────
// صفحة مستقلة لعرض أكواد المشروع.
// ملاحظة مهمة: هاي كانت سابقاً Modal اسمها ProjectCodesModal، ولقينا إنها
// "ميتة" فعلياً — الزر يلي المفروض يفتحها (handleViewCodes بـDashboard.tsx)
// ما كان مربوط بأي مكان بالواجهة، فما كان فيه طريقة توصلها أصلاً.
// حوّلناها هون لصفحة حقيقية بمسارها الخاص ووصلناها بزر فعلي (خطوة ٩).
// ─────────────────────────────────────────────────────────────────────────

const getLanguageIcon = (language: string) => {
  switch (language?.toLowerCase()) {
    case 'python': return '🐍';
    case 'java': return '☕';
    case 'javascript': case 'js': return '🟨';
    case 'typescript': case 'ts': return '🔷';
    default: return '📄';
  }
};

const formatDate = (dateString: string) => {
  if (!dateString) return 'Unknown date';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return 'Unknown date';
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
};

const ProjectCodesPage: React.FC = () => {
  const { project_id } = useParams<{ project_id: string }>();
  const navigate = useNavigate();

  const [codes, setCodes] = useState<ProjectCode[]>([]);
  const [projectName, setProjectName] = useState('Project');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCodes = useCallback(async () => {
    if (!project_id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.projects.getCodes(project_id);
      setCodes(result || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load project codes');
    } finally {
      setLoading(false);
    }
  }, [project_id]);

  useEffect(() => {
    if (!project_id) return;
    apiClient.get(`/api/upm/projects/${project_id}/`)
      .then(res => setProjectName(res.data?.title || res.data?.name || `Project ${project_id}`))
      .catch(() => { /* keep default title — non-critical */ });
  }, [project_id]);

  useEffect(() => { loadCodes(); }, [loadCodes]);

  return (
    <div className="pf-page">
      <div className="pf-topbar">
        <button className="pf-back-btn" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={18} />
          <span>Dashboard</span>
        </button>
        <div className="pf-topbar-center">
          <Code size={20} className="pf-topbar-icon" />
          <span className="pf-topbar-project">{projectName}</span>
          <span className="pf-topbar-sep">/</span>
          <span className="pf-topbar-label">Codes</span>
        </div>
        <div className="pf-topbar-right">
          <button className="pf-icon-btn" onClick={loadCodes} title="Refresh">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="pcp-body">
        {loading ? (
          <div className="pcp-state">
            <div className="pcp-spinner" />
            <p>Loading codes...</p>
          </div>
        ) : error ? (
          <div className="pcp-state">
            <p>{error}</p>
            <button className="pf-retry-btn" onClick={loadCodes}>Retry</button>
          </div>
        ) : codes.length === 0 ? (
          <div className="pcp-state">
            <Code size={64} style={{ opacity: 0.3 }} />
            <h3>No codes uploaded yet</h3>
            <p>Start by adding some code files to this project.</p>
          </div>
        ) : (
          <div className="pcp-codes-list">
            {codes.map((code, index) => (
              <div key={code.id || index} className="pcp-code-card">
                <div className="pcp-code-header">
                  <div className="pcp-code-info">
                    <span className="pcp-lang-icon">{getLanguageIcon(code.language)}</span>
                    <div>
                      <h4 className="pcp-code-name">{code.code_name || `Code ${index + 1}`}</h4>
                      <p className="pcp-file-name">{code.file_name || 'Unknown file'}</p>
                    </div>
                  </div>
                  <div className="pcp-code-meta">
                    <div className="pcp-meta-date">
                      <Calendar size={12} />
                      {formatDate(code.created_at)}
                    </div>
                    {code.language && <span className="pcp-lang-badge">{code.language.toUpperCase()}</span>}
                  </div>
                </div>

                {code.version && <div className="pcp-version">Version: {code.version}</div>}

                <div className="pcp-code-actions">
                  <button className="pcp-btn pcp-btn-view">
                    <FileText size={12} />
                    View Code
                  </button>
                  <button className="pcp-btn pcp-btn-download">
                    <Download size={12} />
                    Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectCodesPage;
