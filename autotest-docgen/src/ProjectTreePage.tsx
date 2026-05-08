import React, { useState, useContext, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Home, LogOut, Sun, Moon, Menu, X,
  Folder, FolderOpen, Lock, User,
  ShieldAlert, HelpCircle, Download, Zap
} from 'lucide-react';
import { AuthContext } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import NotificationBell from './compoents/NotificationBell';
import ProfileModal from './components/ProfileModal/ProfileModal';
import ChangePasswordModal from './components/ChangePasswordModal/ChangePasswordModal';
import SecurityModal from './components/SecurityModal/SecurityModal';
import HelpModal from './components/HelpModal/HelpModal';
import ProjectTree from './components/ProjectTree';
import FileViewer from './components/FileViewer';
import type { FileNode } from './components/ProjectTree';
import apiService from './services/api.service';
import UnifiedApiService from './services/unifiedApiService';
import './Dashboard-Modern.css';
import './Dashboard.css';
import './ProjectTreePage.css';

const ProjectTreePage: React.FC = () => {
  const { project_id } = useParams<{ project_id: string }>();
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const { language, setLanguage } = useLanguage();

  // UI state
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);

  // Tree / viewer state
  const [selectedNode, setSelectedNode] = useState<FileNode | null>(null);

  // Explanation state
  const [projectCodes, setProjectCodes] = useState<any[]>([]);
  const [explanationLevel] = useState<'high' | 'low'>('high');
  const [isNavigating, setIsNavigating] = useState(false);

  useEffect(() => {
    if (project_id) {
      apiService.projects.getCodes(project_id)
        .then(codes => setProjectCodes(codes || []))
        .catch(() => setProjectCodes([]));
    }
  }, [project_id]);

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const handleSelectFile = (node: FileNode) => {
    setSelectedNode(node);
  };

  const handleExplanation = async () => {
    if (!project_id || isNavigating) return;
    setIsNavigating(true);
    try {
      // ── Step 1: fetch the project-level analysis_id from the analyze-project status endpoint
      // This is the ONLY correct source for the project analysis ID.
      let projectAnalysisId: string | null = null;
      let diagramData: any = null;

      try {
        const token = localStorage.getItem('access_token') || '';
        // GET /api/analysis/analyze-project/?project_id={id} returns { analysis_ids: [...], status, ... }
        const statusRes = await fetch(
          `/api/analysis/analyze-project/?project_id=${project_id}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          // analysis_ids is an array of analysis result IDs for this project
          const ids: string[] = statusData.analysis_ids || [];
          if (ids.length > 0) projectAnalysisId = ids[0];
        }
      } catch (_) { /* no analysis yet — user will see the error on ClassDiagramPage */ }

      // ── Step 2: fetch the class diagram data for display
      try {
        const result = await UnifiedApiService.getProjectClassDiagram(project_id);
        if (result?.project_class_diagram) {
          diagramData = result.project_class_diagram;
        }
      } catch (_) { /* no diagram yet */ }

      // ── Step 3: navigate — always pass analysisIds so ClassDiagramPage has the project analysis ID
      navigate('/diagram', {
        state: {
          projectId: project_id,
          codeName: projectCodes[0]?.code_name || 'Project',
          fileName: projectCodes[0]?.file_name || 'project',
          isProjectDiagram: true,
          // Pass the project-level analysis ID — ClassDiagramPage MUST use this, not projectId
          analysisIds: projectAnalysisId ? [projectAnalysisId] : [],
          fromFileTree: true,
          explanationLevel,
          ...(diagramData ? { diagram: diagramData } : {}),
        },
      });
    } catch (_) {
      navigate('/diagram', {
        state: {
          projectId: project_id,
          codeName: 'Project',
          fileName: 'project',
          isProjectDiagram: true,
          analysisIds: [],
          fromFileTree: true,
          explanationLevel,
        },
      });
    } finally {
      setIsNavigating(false);
    }
  };

  const themeClass = isDarkMode ? 'dark' : 'light';
  const dirClass = language === 'ar' ? 'rtl' : 'ltr';

  return (
    <div className={`dashboard ${themeClass} ${dirClass} ${isSidebarOpen ? 'sidebar-open' : ''}`}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="dashboard-header">
        <div className="header-left">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="sidebar-toggle">
            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="logo-section" onClick={() => navigate('/dashboard')} style={{ cursor: 'pointer' }}>
            <Home size={32} className="logo-icon" />
            <span className="logo-text">AutoTestDocGen</span>
          </div>
        </div>

        <div className="header-right">
          <button
            onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
            className="unified-theme-toggle"
            style={{ width: '44px', fontSize: '11px', fontWeight: 700, letterSpacing: '0.03em' }}
          >
            {language === 'en' ? 'AR' : 'EN'}
          </button>

          <button
            onClick={() => { setIsDarkMode(d => { localStorage.setItem('theme', !d ? 'dark' : 'light'); return !d; }); }}
            className="unified-theme-toggle"
          >
            {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <div className="notification-container unified-theme-toggle" style={{ cursor: 'default', overflow: 'visible' }}>
            <NotificationBell userId={user?.id?.toString()} />
          </div>

          <div className="user-section">
            <button onClick={() => setShowUserDropdown(v => !v)} className="unified-theme-toggle">
              <div className="user-avatar">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
            </button>

            {showUserDropdown && (
              <div className="user-dropdown show">
                <div className="dropdown-header">
                  <div className="user-info">
                    <div className="user-avatar">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
                    <div>
                      <div className="user-name">{user?.username || 'User'}</div>
                      <div className="user-email">{user?.email || ''}</div>
                    </div>
                  </div>
                </div>
                <div className="dropdown-items">
                  <button onClick={() => { setShowProfileModal(true); setShowUserDropdown(false); }} className="dropdown-item">
                    <User size={16} />{language === 'ar' ? 'الملف الشخصي' : 'Profile'}
                  </button>
                  <button onClick={() => { setShowChangePasswordModal(true); setShowUserDropdown(false); }} className="dropdown-item">
                    <Lock size={16} />{language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
                  </button>
                  <button onClick={() => { setShowSecurityModal(true); setShowUserDropdown(false); }} className="dropdown-item">
                    <ShieldAlert size={16} />{language === 'ar' ? 'الأمان' : 'Security'}
                  </button>
                  <button onClick={() => { setShowHelpModal(true); setShowUserDropdown(false); }} className="dropdown-item">
                    <HelpCircle size={16} />{language === 'ar' ? 'المساعدة' : 'Help'}
                  </button>
                  <div className="dropdown-divider" />
                  <button onClick={handleLogout} className="dropdown-item logout-item">
                    <LogOut size={16} />{language === 'ar' ? 'تسجيل الخروج' : 'Logout'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className={`dashboard-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <nav className="sidebar-nav">
          <button onClick={() => navigate('/dashboard')} className="nav-item">
            <Folder size={20} />
            <span>{language === 'ar' ? 'المشاريع' : 'Projects'}</span>
          </button>
          <button onClick={() => navigate('/dashboard')} className="nav-item">
            <Download size={20} />
            <span>{language === 'ar' ? 'الملفات المُنشأة' : 'Generated Files'}</span>
          </button>
          <button className="nav-item active">
            <FolderOpen size={20} />
            <span>{language === 'ar' ? 'شجرة الملفات' : 'File Tree'}</span>
          </button>
          <button
            onClick={handleExplanation}
            className="nav-item ptp-explanation-nav"
            disabled={isNavigating}
          >
            <Zap size={20} />
            <span>{language === 'ar' ? 'الشرح والتوثيق' : 'Explanation'}</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
            <div className="user-details">
              <div className="user-name">{user?.username || 'User'}</div>
              <div className="user-role">{language === 'ar' ? 'طالب' : 'Student'}</div>
            </div>
          </div>
          <div className="sidebar-actions">
            <button onClick={() => setShowSecurityModal(true)} className="sidebar-action-btn">
              <Lock size={16} />
              <span>{language === 'ar' ? 'الإعدادات' : 'Settings'}</span>
            </button>
            <button onClick={handleLogout} className="sidebar-action-btn logout-btn">
              <LogOut size={16} />
              <span>{language === 'ar' ? 'تسجيل الخروج' : 'Log Out'}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className={`dashboard-main ${isSidebarOpen ? '' : 'sidebar-closed'}`}>
        <div className="main-content">
          <div className={`ptp-card${isDarkMode ? ' dark' : ' light'}`}>

            {/* Card header */}
            <div className="ptp-card-header">
              <div className="ptp-card-title">
                <FolderOpen size={20} className="ptp-card-icon" />
                <span>{language === 'ar' ? 'شجرة ملفات المشروع' : 'Project File Tree'}</span>
              </div>
              <div className="ptp-header-right">
                {/* Status legend */}
                <div className="ptp-legend">
                  <span className={`pt-status-badge pt-status-modified${isDarkMode ? ' dark' : ''}`}>M</span>
                  <span className="ptp-legend-label">{language === 'ar' ? 'معدّل' : 'Modified'}</span>
                  <span className={`pt-status-badge pt-status-added${isDarkMode ? ' dark' : ''}`}>U</span>
                  <span className="ptp-legend-label">{language === 'ar' ? 'جديد' : 'Added'}</span>
                </div>
                <button className="ptp-back-btn" onClick={() => navigate('/dashboard')}>
                  {language === 'ar' ? '← لوحة التحكم' : '← Dashboard'}
                </button>
              </div>
            </div>

            {/* Card body: tree + viewer */}
            <div className="ptp-body">
              <div className="ptp-tree-col">
                <ProjectTree
                  projectId={project_id || ''}
                  selectedNodeId={selectedNode?.id || selectedNode?.filepath || null}
                  onSelectFile={handleSelectFile}
                  isDarkMode={isDarkMode}
                />
              </div>
              <div className="ptp-viewer-col">
                <FileViewer
                  projectId={project_id || ''}
                  selectedNode={selectedNode}
                  isDarkMode={isDarkMode}
                />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ── Modals ──────────────────────────────────────────────────────── */}
      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        user={user}
        onSave={() => setShowProfileModal(false)}
        isLoading={false}
      />
      <ChangePasswordModal
        isOpen={showChangePasswordModal}
        onClose={() => setShowChangePasswordModal(false)}
        isLoading={false}
      />
      <SecurityModal
        isOpen={showSecurityModal}
        onClose={() => setShowSecurityModal(false)}
        language={language}
      />
      <HelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
        language={language}
      />
    </div>
  );
};

export default ProjectTreePage;
