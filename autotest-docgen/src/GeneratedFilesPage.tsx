import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from './services/api.service';
import './GeneratedFilesPage.css';

interface GeneratedFile {
  _id: string;
  filename: string;
  file_type: 'pdf' | 'markdown' | 'html' | 'xml';
  file_size: number;
  created_at: string;
  downloaded_count: number;
  analysis_id: string;
  explanation_id: string;
}

type ViewMode = 'grid' | 'list';
type PageMode = 'files' | 'display';

// ── SVG Icons ────────────────────────────────────────────────────────
const IconFolder = () => (
  <svg viewBox="0 0 24 24" style={{ width: 32, height: 32, color: 'var(--pt-grad-a)' }}>
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

const IconCode = ({ size = 14 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" style={{ width: size, height: size }}>
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

const IconFile = ({ size = 14 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" style={{ width: size, height: size }}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const IconPdf = () => (
  <svg viewBox="0 0 24 24" style={{ width: 20, height: 20 }}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="#ef4444" />
    <path d="M8 12h8v2H8zm0-4h8v2H8z" fill="white" />
    <polyline points="14 2 14 8 20 8" stroke="#ef4444" strokeWidth="2" fill="none" />
  </svg>
);

const IconHtml = () => (
  <svg viewBox="0 0 24 24" style={{ width: 20, height: 20 }}>
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#f97316" />
    <polyline points="13 2 13 9 20 9" stroke="#f97316" strokeWidth="2" fill="none" />
    <text x="12" y="16" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold" fontFamily="monospace">&lt;/&gt;</text>
  </svg>
);

const IconXml = () => (
  <svg viewBox="0 0 24 24" style={{ width: 20, height: 20 }}>
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#a855f7" />
    <polyline points="13 2 13 9 20 9" stroke="#a855f7" strokeWidth="2" fill="none" />
    <text x="12" y="16" textAnchor="middle" fill="white" fontSize="6" fontWeight="bold" fontFamily="monospace">XML</text>
  </svg>
);

const IconMd = () => (
  <svg viewBox="0 0 24 24" style={{ width: 20, height: 20 }}>
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#3b82f6" />
    <polyline points="13 2 13 9 20 9" stroke="#3b82f6" strokeWidth="2" fill="none" />
    <text x="12" y="16" textAnchor="middle" fill="white" fontSize="6" fontWeight="bold" fontFamily="monospace">MD</text>
  </svg>
);

const IconCodeFile = () => (
  <svg viewBox="0 0 24 24" style={{ width: 20, height: 20 }}>
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" fill="#22c55e" />
    <polyline points="13 2 13 9 20 9" stroke="#22c55e" strokeWidth="2" fill="none" />
    <text x="12" y="16" textAnchor="middle" fill="white" fontSize="6" fontWeight="bold" fontFamily="monospace">&lt;/&gt;</text>
  </svg>
);

const IconEye = ({ size = 12 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" style={{ width: size, height: size }}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const IconDownload = ({ size = 12 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" style={{ width: size, height: size }}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const IconGrid = () => (
  <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }}>
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);

const IconList = () => (
  <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }}>
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" />
    <line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
);

const IconArrowLeft = ({ size = 16 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" style={{ width: size, height: size }}>
    <line x1="19" y1="12" x2="5" y2="12" />
    <polyline points="12 19 5 12 12 5" />
  </svg>
);

// ── Helpers ──────────────────────────────────────────────────────────
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const formatDate = (dateString: string): string => {
  if (!dateString) return '\u2014';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return '\u2014';
  const d = date.getDate();
  const m = date.getMonth() + 1;
  const y = date.getFullYear();
  // Use explicit string concat to avoid locale-specific RTL/LTR marks
  return d.toString() + '/' + m.toString() + '/' + y.toString();
};

const getFileIconClass = (fileType: string, filename?: string): string => {
  // Extension from filename is the ground truth — always wins over file_type
  const ext = (filename || '').split('.').pop()?.toLowerCase() || '';
  if (ext === 'pdf')                return 'icon-pdf';
  if (ext === 'html' || ext === 'htm') return 'icon-html';
  if (ext === 'xml')                return 'icon-xml';
  if (ext === 'md')                 return 'icon-md';
  if (['py','js','ts','tsx','jsx','java','go','rs','rb','php','cs','kt','cpp','c'].includes(ext)) return 'icon-code';
  // Fallback to file_type only when no usable extension
  const t = (fileType || '').toLowerCase();
  if (t === 'pdf')      return 'icon-pdf';
  if (t === 'html')     return 'icon-html';
  if (t === 'xml')      return 'icon-xml';
  if (t === 'markdown' || t === 'md') return 'icon-md';
  return 'icon-code';
};

const getFileExt = (fileType: string, filename?: string): string => {
  const ext = (filename || '').split('.').pop()?.toLowerCase() || '';
  if (ext === 'pdf')                return 'pdf';
  if (ext === 'html' || ext === 'htm') return 'html';
  if (ext === 'xml')                return 'xml';
  if (ext === 'md')                 return 'md';
  const t = (fileType || '').toLowerCase();
  if (t === 'pdf')      return 'pdf';
  if (t === 'html')     return 'html';
  if (t === 'xml')      return 'xml';
  if (t === 'markdown' || t === 'md') return 'md';
  return ext || t.split('/').pop()?.slice(0, 4) || t;
};

const getFileIconLabel = (fileType: string, filename?: string): string => {
  const ext = (filename || '').split('.').pop()?.toLowerCase() || '';
  if (ext === 'pdf')                return 'PDF';
  if (ext === 'html' || ext === 'htm') return 'HTM';
  if (ext === 'xml')                return 'XML';
  if (ext === 'md')                 return 'MD';
  const t = (fileType || '').toLowerCase();
  if (t === 'pdf')      return 'PDF';
  if (t === 'html')     return 'HTM';
  if (t === 'xml')      return 'XML';
  if (t === 'markdown' || t === 'md') return 'MD';
  return (ext || t.split('/').pop() || t).toUpperCase().slice(0, 3);
};

interface FileActionsProps {
  file: GeneratedFile;
  onView: (f: GeneratedFile) => void;
  onDownload: (f: GeneratedFile) => void;
  date: string;
}

const GridFileItem: React.FC<FileActionsProps> = ({ file, onView, onDownload, date }) => {
  const iconClass = getFileIconClass(file.file_type, file.filename);
  const getFileIcon = () => {
    const ext = (file.filename || '').split('.').pop()?.toLowerCase() || '';
    if (ext === 'pdf') return <IconPdf />;
    if (ext === 'html' || ext === 'htm') return <IconHtml />;
    if (ext === 'xml') return <IconXml />;
    if (ext === 'md') return <IconMd />;
    return <IconCodeFile />;
  };
  
  return (
    <div className="gfp-file-item">
      <div className="file-top">
        <div className={`gfp-file-icon ${iconClass}`}>
          {getFileIcon()}
        </div>
        <div className="file-details">
          <div className="gfp-file-name" title={file.filename}>{file.filename}</div>
          <div className="gfp-file-meta">{formatFileSize(file.file_size)} · .{getFileExt(file.file_type, file.filename)}</div>
        </div>
      </div>
      <div className="gfp-file-actions">
        <span className="gfp-file-date">{date}</span>
        <div className="action-buttons">
          <button className="btn-sm btn-view" onClick={() => onView(file)}>
            <IconEye /> View
          </button>
          <button className="btn-sm btn-download" onClick={() => onDownload(file)}>
            <IconDownload /> Save
          </button>
        </div>
      </div>
    </div>
  );
};

interface ProjectSectionProps {
  projectName: string;
  projectDate: string;
  files: GeneratedFile[];
  onView: (f: GeneratedFile) => void;
  onDownload: (f: GeneratedFile) => void;
}

const ProjectSection: React.FC<ProjectSectionProps> = ({ projectName, projectDate, files, onView, onDownload }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  return (
    <div className="gfp-project-card">
      <div className="gfp-card-header">
        <div className="project-info">
          <div className="project-name">
            <div className="project-icon">
              <IconCode size={14} />
            </div>
            {projectName}
          </div>
          <div className="project-meta">
            <span>Created: {projectDate}</span>
            <span className="meta-sep">|</span>
            <span>{files.length} {files.length === 1 ? 'File' : 'Files'}</span>
          </div>
        </div>
        <div className="view-toggle">
          <button
            className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            <IconGrid /> Grid
          </button>
          <button
            className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <IconList /> List
          </button>
        </div>
      </div>

      <div className="gfp-card-body">
        {/* Grid View */}
        <div className={`gfp-files-grid ${viewMode !== 'grid' ? 'hidden' : ''}`}>
          {files.map(file => (
            <GridFileItem
              key={file._id}
              file={file}
              onView={onView}
              onDownload={onDownload}
              date={formatDate(file.created_at)}
            />
          ))}
        </div>

        {/* List View */}
        <div className={`gfp-files-list ${viewMode !== 'list' ? 'hidden' : ''}`}>
          <table className="list-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Type</th>
                <th>Size</th>
                <th>Date</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map(file => (
                <tr key={file._id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className={`list-file-icon ${getFileIconClass(file.file_type, file.filename)}`}>
                        {(() => {
                          const ext = (file.filename || '').split('.').pop()?.toLowerCase() || '';
                          if (ext === 'pdf') return <IconPdf />;
                          if (ext === 'html' || ext === 'htm') return <IconHtml />;
                          if (ext === 'xml') return <IconXml />;
                          if (ext === 'md') return <IconMd />;
                          return <IconCodeFile />;
                        })()}
                      </div>
                      {file.filename}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.7 }}>
                      .{getFileExt(file.file_type, file.filename)}
                    </span>
                  </td>
                  <td>{formatFileSize(file.file_size)}</td>
                  <td>{formatDate(file.created_at)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <div className="action-buttons" style={{ justifyContent: 'flex-end' }}>
                      <button className="btn-sm btn-view" onClick={() => onView(file)}>View</button>
                      <button className="btn-sm btn-download" onClick={() => onDownload(file)}>Save</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────
const GeneratedFilesPage: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<GeneratedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageMode, setPageMode] = useState<PageMode>('files');
  const [selectedFile, setSelectedFile] = useState<GeneratedFile | null>(null);
  const [displayContent, setDisplayContent] = useState<string>('');
  const [loadingDisplay, setLoadingDisplay] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const themeClass = isDarkMode ? 'dark' : 'light';

  // Sync html element class so index.css body rules apply correctly
  useEffect(() => {
    const html = document.documentElement;
    if (isDarkMode) {
      html.classList.add('dark');
      html.classList.remove('light');
    } else {
      html.classList.add('light');
      html.classList.remove('dark');
    }
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.analysis.getGeneratedFiles();
      const arr = Array.isArray(data) ? data : [];
      setFiles(arr);
    } catch (err) {
      console.error('Error fetching files:', err);
      setError('Failed to load generated files');
    } finally {
      setLoading(false);
    }
  };

  const handleView = async (file: GeneratedFile) => {
    try {
      setLoadingDisplay(true);
      setSelectedFile(file);
      setPageMode('display');
      setPdfBlobUrl(null);
      setDisplayContent('');

      const blob = await apiService.analysis.downloadFile(file._id);

      if (file.file_type === 'pdf') {
        const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
        setPdfBlobUrl(url);
      } else {
        const text = await new Blob([blob]).text();
        setDisplayContent(text);
      }
    } catch (err) {
      console.error('Error displaying file:', err);
      setError('Failed to load file content');
    } finally {
      setLoadingDisplay(false);
    }
  };

  // Cleanup blob URL on unmount or when leaving display mode
  const handleBackToFiles = () => {
    if (pdfBlobUrl) {
      window.URL.revokeObjectURL(pdfBlobUrl);
      setPdfBlobUrl(null);
    }
    setPageMode('files');
  };

  const handleDownload = async (file: GeneratedFile) => {
    try {
      const blob = await apiService.analysis.downloadFile(file._id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading file:', err);
      setError('Failed to download file. Please try again.');
    }
  };

  useEffect(() => { fetchFiles(); }, []);

  // Group files by analysis_id (project)
  const grouped = files.reduce<Record<string, GeneratedFile[]>>((acc, file) => {
    const key = file.analysis_id || 'unknown';
    if (!acc[key]) acc[key] = [];
    acc[key].push(file);
    return acc;
  }, {});

  // ── Loading ──
  if (loading) {
    return (
      <div className={`gfp-container ${themeClass}`}>
        <div className="gfp-loading">
          <div className="gfp-spinner" />
          <p>Loading generated files...</p>
        </div>
      </div>
    );
  }

  // ── Error (no files) ──
  if (error && files.length === 0) {
    return (
      <div className={`gfp-container ${themeClass}`}>
        <div className="gfp-error">
          <p style={{ color: '#f87171' }}>{error}</p>
          <button className="gfp-retry-btn" onClick={fetchFiles}>Retry</button>
        </div>
      </div>
    );
  }

  // ── Display Mode ──
  if (pageMode === 'display' && selectedFile) {
    return (
      <div className={`gfp-container ${themeClass}`}>
        <div className="gfp-display-mode">
          <div className="gfp-display-header">
            <button className="gfp-back-btn" onClick={handleBackToFiles}>
              <IconArrowLeft /> Back to Files
            </button>
            <h2 className="gfp-display-title">{selectedFile.filename}</h2>
            <button className="btn-sm btn-download" onClick={() => handleDownload(selectedFile)}>
              <IconDownload size={12} /> Download
            </button>
          </div>

          <div className="gfp-content-box">
            {loadingDisplay ? (
              <div className="gfp-loading">
                <div className="gfp-spinner" />
                <p>Loading content...</p>
              </div>
            ) : selectedFile.file_type === 'pdf' && pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                className="gfp-pdf-viewer"
                title={selectedFile.filename}
              />
            ) : selectedFile.file_type === 'markdown' ? (
              <div className="gfp-markdown"><pre>{displayContent}</pre></div>
            ) : selectedFile.file_type === 'html' ? (
              <iframe
                srcDoc={displayContent}
                className="gfp-pdf-viewer"
                title={selectedFile.filename}
                sandbox="allow-same-origin"
              />
            ) : selectedFile.file_type === 'xml' ? (
              <div className="gfp-markdown"><pre>{displayContent}</pre></div>
            ) : (
              <div className="gfp-pdf-placeholder">
                <IconFile size={48} />
                <p>Failed to load file. Please download it instead.</p>
                <button className="gfp-dashboard-btn" onClick={() => handleDownload(selectedFile)}>
                  Download File
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ── Files List ──
  return (
    <div className={`gfp-container ${themeClass}`}>
      <header className="gfp-page-header">
        <div className="gfp-header-left">
          <button className="gfp-back-btn" onClick={() => navigate('/dashboard')}>
            <IconArrowLeft /> Dashboard
          </button>
          <div className="gfp-main-title">
            <IconFolder />
            <span>Generated Files</span>
          </div>
        </div>
        <button
          className="gfp-theme-btn"
          onClick={() => setIsDarkMode(d => {
            localStorage.setItem('theme', !d ? 'dark' : 'light');
            return !d;
          })}
          title={isDarkMode ? 'Light Mode' : 'Dark Mode'}
        >
          {isDarkMode
            ? <svg viewBox="0 0 24 24" style={{ width: 16, height: 16 }}><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>
            : <svg viewBox="0 0 24 24" style={{ width: 16, height: 16 }}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
          }
          {isDarkMode ? 'Light' : 'Dark'}
        </button>
      </header>

      {files.length === 0 ? (
        <div className="gfp-empty">
          <div className="gfp-empty-icon"><IconFile size={64} /></div>
          <h3>No generated files found</h3>
          <p>Generate some documentation files first to see them here.</p>
          <button className="gfp-dashboard-btn" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </button>
        </div>
      ) : (
        Object.entries(grouped).map(([projectId, projectFiles]) => (
          <ProjectSection
            key={projectId}
            projectName={projectFiles[0]?.filename?.split('_')[0] || `Project ${projectId.slice(-6)}`}
            projectDate={formatDate(projectFiles[0]?.created_at)}
            files={projectFiles}
            onView={handleView}
            onDownload={handleDownload}
          />
        ))
      )}
    </div>
  );
};

export default GeneratedFilesPage;
