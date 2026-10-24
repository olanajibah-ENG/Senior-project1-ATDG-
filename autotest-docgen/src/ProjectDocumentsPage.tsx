import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Calendar, Eye, RefreshCw } from 'lucide-react';
import apiService, { type ProjectDocumentation } from './services/api.service';
import apiClient from './services/apiClient';
import './ProjectFilesPage.css';
import './ProjectCodesPage.css'; // نعيد استخدام نفس أنماط الحالة (loading/error/empty) بدل تكرارها

// ─────────────────────────────────────────────────────────────────────────
// صفحة مستقلة لعرض مستندات المشروع (تقارير، رسوم بيانية، شروحات).
// كانت سابقاً Modal اسمها ProjectDocumentsModal — ولقينا إنها "ميتة" فعلياً:
// - قائمة documents ما كانت تتعبى من أي API call (بقيت [] دايماً)
// - onDocumentClick ما كان موصول لأي منطق فعلي
// - ولا زر بالواجهة كان يفتحها أصلاً
// حوّلناها هون لصفحة حقيقية موصولة بـapiService.projects.getDocs() الموجود
// أصلاً بالـservices بس ما كان مستخدم (خطوة ٩).
// ─────────────────────────────────────────────────────────────────────────

const getDocumentIcon = (type: string) => {
  switch (type) {
    case 'class_diagram': return '📊';
    case 'logic_explanation': return '📝';
    case 'documentation': return '📄';
    default: return '📁';
  }
};

const getDocumentTypeLabel = (type: string) => {
  switch (type) {
    case 'class_diagram': return 'Class Diagram';
    case 'logic_explanation': return 'Logic Explanation';
    case 'documentation': return 'Documentation';
    default: return 'Document';
  }
};

const formatDate = (dateString: string) => {
  if (!dateString) return 'Unknown date';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return 'Unknown date';
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
};

const ProjectDocumentsPage: React.FC = () => {
  const { project_id } = useParams<{ project_id: string }>();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<ProjectDocumentation[]>([]);
  const [projectName, setProjectName] = useState('Project');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    if (!project_id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.projects.getDocs(project_id);
      setDocuments(result || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load project documents');
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

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  const handleViewDocument = async (doc: ProjectDocumentation) => {
    try {
      const res = await apiClient.get(`/api/analysis/download-generated-file/${doc.id}/`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data as Blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (err) {
      console.error('Failed to open document:', err);
    }
  };

  return (
    <div className="pf-page">
      <div className="pf-topbar">
        <button className="pf-back-btn" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={18} />
          <span>Dashboard</span>
        </button>
        <div className="pf-topbar-center">
          <FileText size={20} className="pf-topbar-icon" />
          <span className="pf-topbar-project">{projectName}</span>
          <span className="pf-topbar-sep">/</span>
          <span className="pf-topbar-label">Documents</span>
        </div>
        <div className="pf-topbar-right">
          <button className="pf-icon-btn" onClick={loadDocuments} title="Refresh">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="pcp-body">
        {loading ? (
          <div className="pcp-state">
            <div className="pcp-spinner" />
            <p>Loading documents...</p>
          </div>
        ) : error ? (
          <div className="pcp-state">
            <p>{error}</p>
            <button className="pf-retry-btn" onClick={loadDocuments}>Retry</button>
          </div>
        ) : documents.length === 0 ? (
          <div className="pcp-state">
            <FileText size={64} style={{ opacity: 0.3 }} />
            <h3>No documents yet</h3>
            <p>Generate a class diagram or explanation to see documents here.</p>
          </div>
        ) : (
          <div className="pcp-codes-list">
            {documents.map((doc) => (
              <div key={doc.id} className="pcp-code-card">
                <div className="pcp-code-header">
                  <div className="pcp-code-info">
                    <span className="pcp-lang-icon">{getDocumentIcon(doc.type)}</span>
                    <div>
                      <h4 className="pcp-code-name">{doc.name}</h4>
                      <p className="pcp-file-name">{getDocumentTypeLabel(doc.type)}</p>
                    </div>
                  </div>
                  <div className="pcp-code-meta">
                    <div className="pcp-meta-date">
                      <Calendar size={12} />
                      {formatDate(doc.created_at)}
                    </div>
                  </div>
                </div>

                <div className="pcp-code-actions">
                  <button className="pcp-btn pcp-btn-view" onClick={() => handleViewDocument(doc)}>
                    <Eye size={12} />
                    View
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

export default ProjectDocumentsPage;
