﻿import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LogOut, Home, User, Lock,
    HelpCircle, Sun, Moon, Plus,
    Folder, ShieldAlert,
    Menu, X, Edit, Trash2, Download, Eye, FileText,
    AlertCircle, CheckCircle
} from 'lucide-react';

import { type Project, type PaginatedResponse, type UpdateProjectData, formatApiError } from './services/api.service';
import apiService from './services/api.service';
import UnifiedApiService from './services/unifiedApiService';
import { AuthContext } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import CodeUploadForm from './compoents/ProjectCutomizationModal/CodeUploadForm';
import AnalysisOverlay from './compoents/ProjectCutomizationModal/AnalysisOverlay';
import { useAlert } from './compoents/Alert/useAlert';
import NotificationBell from './compoents/NotificationBell';
import ChatWidget from './components/ChatWidget/ChatWidget';
import ProjectDocumentsModal from './compoents/ProjectDocumentsModal/ProjectDocumentsModal';
import ProjectCodesModal from './compoents/ProjectCodesModal/ProjectCodesModal';
import ProfileModal from './components/ProfileModal/ProfileModal';
import ChangePasswordModal from './components/ChangePasswordModal/ChangePasswordModal';
import SecurityModal from './components/SecurityModal/SecurityModal';
import HelpModal from './components/HelpModal/HelpModal';
import './Dashboard-Modern.css';
import './Dashboard.css';
import './Dashboard-Header-Fix.css';

// Edit Project Form Component
const EditProjectForm: React.FC<{
    project: Project;
    onSubmit: (data: UpdateProjectData) => void;
    onClose: () => void;
    isLoading: boolean;
    apiError: string | null;
    isDark?: boolean;
    lang?: string;
}> = ({ project, onSubmit, onClose, isLoading, apiError, isDark = false, lang = 'en' }) => {
    const [title, setTitle] = useState(project.title);
    const [description, setDescription] = useState(project.description);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, description });
    };

    const ar = lang === 'ar';

    return (
        <div className="pf-overlay" onClick={onClose}>
            <div className={`pf-modal ${isDark ? 'dark' : 'light'}`} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="pf-header">
                    <div className="pf-header-icon">
                        <Edit size={20} />
                    </div>
                    <div className="pf-header-text">
                        <h2 className="pf-title">{ar ? 'تعديل المشروع' : 'Edit Project'}</h2>
                        <p className="pf-subtitle">{ar ? 'حدّث اسم المشروع أو وصفه' : 'Update the project title or description'}</p>
                    </div>
                    <button className="pf-close-btn" onClick={onClose} title="Close">
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} className="pf-body">

                    {apiError && (
                        <div className="pf-error-banner">
                            <AlertCircle size={14} />
                            {apiError}
                        </div>
                    )}

                    <div className="pf-field">
                        <label className="pf-label">
                            {ar ? 'العنوان' : 'Title'}
                            <span className="pf-required">*</span>
                        </label>
                        <input
                            className="pf-input"
                            type="text"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            placeholder={ar ? 'اسم المشروع...' : 'Project title...'}
                            required
                            autoFocus
                        />
                    </div>

                    <div className="pf-field">
                        <label className="pf-label">{ar ? 'الوصف' : 'Description'}</label>
                        <textarea
                            className="pf-input pf-textarea"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder={ar ? 'وصف مختصر للمشروع...' : 'Short project description...'}
                            rows={3}
                        />
                    </div>

                    {/* Actions */}
                    <div className="pf-actions">
                        <button type="button" className="pf-btn-cancel" onClick={onClose} disabled={isLoading}>
                            {ar ? 'إلغاء' : 'Cancel'}
                        </button>
                        <button type="submit" className="pf-btn-submit" disabled={isLoading}>
                            {isLoading
                                ? <><span className="pf-spinner" />{ar ? 'جاري الحفظ...' : 'Saving...'}</>
                                : <><CheckCircle size={15} />{ar ? 'حفظ التغييرات' : 'Save Changes'}</>
                            }
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Create Project Form Component
const CreateProjectForm: React.FC<{
    onSubmit: (data: { title: string; description: string }) => void;
    onClose: () => void;
    isLoading: boolean;
    apiError: string | null;
    isDark?: boolean;
    lang?: string;
}> = ({ onSubmit, onClose, isLoading, apiError, isDark = false, lang = 'en' }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, description });
    };

    const ar = lang === 'ar';

    return (
        <div className="pf-overlay" onClick={onClose}>
            <div className={`pf-modal ${isDark ? 'dark' : 'light'}`} onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="pf-header">
                    <div className="pf-header-icon">
                        <Plus size={20} />
                    </div>
                    <div className="pf-header-text">
                        <h2 className="pf-title">{ar ? 'إنشاء مشروع جديد' : 'Create New Project'}</h2>
                        <p className="pf-subtitle">{ar ? 'أعطِ مشروعك اسماً واضحاً ووصفاً مختصراً' : 'Give your project a clear name and a short description'}</p>
                    </div>
                    <button className="pf-close-btn" onClick={onClose} title="Close">
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} className="pf-body">

                    {apiError && (
                        <div className="pf-error-banner">
                            <AlertCircle size={14} />
                            {apiError}
                        </div>
                    )}

                    <div className="pf-field">
                        <label className="pf-label">
                            {ar ? 'العنوان' : 'Title'}
                            <span className="pf-required">*</span>
                        </label>
                        <input
                            className="pf-input"
                            type="text"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            placeholder={ar ? 'مثال: نظام إدارة الطلاب' : 'e.g. Student Management System'}
                            required
                            autoFocus
                        />
                    </div>

                    <div className="pf-field">
                        <label className="pf-label">{ar ? 'الوصف' : 'Description'}</label>
                        <textarea
                            className="pf-input pf-textarea"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder={ar ? 'وصف مختصر للمشروع (اختياري)...' : 'Short project description (optional)...'}
                            rows={3}
                        />
                        <span className="pf-hint">{ar ? 'اختياري — يمكنك تركه فارغاً' : 'Optional — you can leave this empty'}</span>
                    </div>

                    {/* Actions */}
                    <div className="pf-actions">
                        <button type="button" className="pf-btn-cancel" onClick={onClose} disabled={isLoading}>
                            {ar ? 'إلغاء' : 'Cancel'}
                        </button>
                        <button type="submit" className="pf-btn-submit" disabled={isLoading || !title.trim()}>
                            {isLoading
                                ? <><span className="pf-spinner" />{ar ? 'جاري الإنشاء...' : 'Creating...'}</>
                                : <><Plus size={15} />{ar ? 'إنشاء المشروع' : 'Create Project'}</>
                            }
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// â”€â”€ DashProjectSection â€” per-project card with Grid/List toggle â”€â”€â”€â”€â”€â”€
const DashProjectSection: React.FC<{
    projectName: string;
    files: any[];
    onView: (f: any) => void;
    onDownload: (f: any) => void;
    isDark: boolean;
    lang: string;
}> = ({ projectName, files, onView, onDownload, isDark, lang }) => {
    const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid');

    const fmt = (bytes: number) => {
        if (!bytes) return 'â€”';
        const k = 1024, s = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + s[i];
    };

    const fmtDate = (d: string) => { if (!d) return '—'; const dt = new Date(d); if (isNaN(dt.getTime())) return '—'; return dt.getDate().toString() + '/' + (dt.getMonth() + 1).toString() + '/' + dt.getFullYear().toString(); };

    return (
        <div className={`dash-proj-card${isDark ? ' dark' : ' light'}`}>
            {/* Card header */}
            <div className="dash-proj-header">
                <div>
                    <div className="dash-proj-name">{projectName}</div>
                    <div className="dash-proj-meta">
                        {files.length} {lang === 'ar' ? 'ملف' : 'files'}
                    </div>
                </div>
                <div className="dash-view-toggle">
                    <button
                        className={`dash-view-btn${viewMode === 'grid' ? ' active' : ''}`}
                        onClick={() => setViewMode('grid')}
                        title="Grid"
                    >
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
                            <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
                        </svg>
                        Grid
                    </button>
                    <button
                        className={`dash-view-btn${viewMode === 'list' ? ' active' : ''}`}
                        onClick={() => setViewMode('list')}
                        title="List"
                    >
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" />
                            <line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" />
                            <line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
                        </svg>
                        List
                    </button>
                </div>
            </div>

            {/* Grid view */}
            {viewMode === 'grid' && (
                <div className="dash-files-grid">
                    {files.map((file: any, i: number) => (
                        <div key={file._id || i} className="dash-file-card">
                            <div className="dash-file-top">
                                <div className={`dash-file-icon ${file.type === 'pdf' ? 'icon-pdf' : 'icon-md'}`}>
                                    {file.type === 'pdf' ? 'PDF' : 'MD'}
                                </div>
                                <div className="dash-file-info">
                                    <div className="dash-file-name" title={file.name}>{file.name}</div>
                                    <div className="dash-file-meta">{fmt(file.file_size)} · {file.type?.toUpperCase()}</div>
                                </div>
                            </div>
                            <div className="dash-file-footer">
                                <span className="dash-file-date">{fmtDate(file.created_at)}</span>
                                <div className="dash-file-btns">
                                    <button className="dash-btn-view" onClick={() => onView(file)} title="View">
                                        <Eye size={14} />
                                    </button>
                                    <button className="dash-btn-dl" onClick={() => onDownload(file)} title="Download">
                                        <Download size={14} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* List view */}
            {viewMode === 'list' && (
                <div className="dash-files-list">
                    <table className="dash-list-table">
                        <thead>
                            <tr>
                                <th>{lang === 'ar' ? 'الاسم' : 'Name'}</th>
                                <th>{lang === 'ar' ? 'النوع' : 'Type'}</th>
                                <th>{lang === 'ar' ? 'الحجم' : 'Size'}</th>
                                <th>{lang === 'ar' ? 'التاريخ' : 'Date'}</th>
                                <th style={{ textAlign: 'right' }}>{lang === 'ar' ? 'ط¥ط¬ط±ط§ط،ط§طھ' : 'Actions'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {files.map((file: any, i: number) => (
                                <tr key={file._id || i}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span className={`dash-file-icon-sm ${file.type === 'pdf' ? 'icon-pdf' : 'icon-md'}`}>
                                                {file.type === 'pdf' ? 'PDF' : 'MD'}
                                            </span>
                                            <span className="dash-file-name-sm">{file.name}</span>
                                        </div>
                                    </td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', opacity: 0.7 }}>
                                        .{file.type === 'markdown' ? 'md' : file.type}
                                    </td>
                                    <td>{fmt(file.file_size)}</td>
                                    <td>{fmtDate(file.created_at)}</td>
                                    <td style={{ textAlign: 'right' }}>
                                        <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                                            <button className="dash-btn-view" onClick={() => onView(file)} title="View">
                                                <Eye size={13} />
                                            </button>
                                            <button className="dash-btn-dl" onClick={() => onDownload(file)} title="Download">
                                                <Download size={13} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};


const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const { user, logout } = useContext(AuthContext);
    const { language, setLanguage } = useLanguage();
    const { showAlert, AlertComponent } = useAlert();

    // State management
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectsError, setProjectsError] = useState<string | null>(null);
    const [isLoadingProjects, setIsLoadingProjects] = useState(true);
    const [activeAction, setActiveAction] = useState<'projects' | 'documents'>('projects');
    const [showEditModal, setShowEditModal] = useState(false);
    const [showCodeModal, setShowCodeModal] = useState(false);
    const [editingProject, setEditingProject] = useState<Project | null>(null);
    const [codeProject, setCodeProject] = useState<Project | null>(null);
    const [isCodeProcessing, setIsCodeProcessing] = useState(false);
    const [codeError, setCodeError] = useState<string | null>(null);

    // Generated Files State
    const [generatedFiles, setGeneratedFiles] = useState<any[]>([]);
    const [isLoadingFiles, setIsLoadingFiles] = useState(false);
    const [filesError, setFilesError] = useState<string | null>(null);

    // UI State
    const [isDarkMode, setIsDarkMode] = useState(() => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) return savedTheme === 'dark';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
    const [showSecurityModal, setShowSecurityModal] = useState(false);
    const [showHelpModal, setShowHelpModal] = useState(false);
    const [showUserDropdown, setShowUserDropdown] = useState(false);
    const [showCreateProjectModal, setShowCreateProjectModal] = useState(false);
    const [showCodesModal, setShowCodesModal] = useState(false);
    const [showDocumentsModal, setShowDocumentsModal] = useState(false);
    const [projectDocuments, setProjectDocuments] = useState<any[]>([]);
    const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [projectCodes, setProjectCodes] = useState<any[]>([]);
    const [isLoadingCodes, setIsLoadingCodes] = useState(false);
    const [showAnalysis, setShowAnalysis] = useState(false);

    // Theme handling
    useEffect(() => {
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
        } else {
            document.documentElement.classList.add('light');
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    }, [isDarkMode]);

    // Language handling
    useEffect(() => {
        document.documentElement.lang = language;
        document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    }, [language]);

    // Fetch projects
    const fetchProjects = async () => {
        setIsLoadingProjects(true);
        setProjectsError(null);
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                navigate('/auth');
                return;
            }

            console.log('ًں”„ Fetching projects...');
            const response: PaginatedResponse<Project> = await apiService.projects.list();
            console.log('ًں“ٹ API Response:', response);

            if (response && response.results && Array.isArray(response.results)) {
                console.log('âœ… Projects loaded:', response.results.length, 'projects');
                setProjects(response.results);
            } else if (response && Array.isArray(response)) {
                console.log('âœ… Projects loaded (direct array):', response.length, 'projects');
                setProjects(response);
            } else {
                console.error("â‌Œ API response missing 'results' array or invalid structure:", response);
                setProjectsError('Invalid data structure received from server.');
                setProjects([]);
            }
        } catch (err: any) {
            console.error('â‌Œ Failed to fetch projects:', err);

            if (err.response?.status === 401) {
                console.log('ًں”گ Authentication failed, clearing tokens and redirecting...');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                setProjectsError('Session expired. Please login again.');
                navigate('/auth');
                return;
            }

            const errorMessage = formatApiError(err);
            setProjectsError(errorMessage);
            setProjects([]);
        } finally {
            setIsLoadingProjects(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    // Fetch generated files â€” fetch all then filter by user's projects
    const fetchGeneratedFiles = async () => {
        console.log('ًں”„ Fetching generated files...');
        setIsLoadingFiles(true);
        setFilesError(null);
        try {
            const token = localStorage.getItem('access_token') || '';
            const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

            // Fetch all generated files (backend filters by authenticated user automatically)
            const res = await fetch('/api/analysis/generated-files/', { headers });
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            const data = await res.json();
            const raw: any[] = Array.isArray(data) ? data : data.files || data.results || [];

            // Build a lookup of user's project IDs â†’ project title
            const projectMap = new Map(projects.map(p => [p.id, p.title]));
            const userProjectIds = new Set(projects.map(p => p.id));

            // Keep only files that belong to one of the user's projects
            const files = raw
                .filter((file: any) => {
                    const pid = file.project_id || file.source_project_id;
                    // If file has a project_id, filter by it; otherwise keep all (backend already filtered)
                    return !pid || userProjectIds.has(pid);
                })
                .map((file: any) => {
                    const pid = file.project_id || file.source_project_id;
                    return {
                        ...file,
                        name: file.filename || file.file_name || 'Unknown',
                        type: file.file_type || (file.filename?.endsWith('.pdf') ? 'pdf' : 'markdown'),
                        projectName: (pid && projectMap.get(pid)) || `Project ${(file.analysis_id || pid || '').slice(-6)}`,
                        projectId: pid || file.analysis_id || 'unknown',
                    };
                });

            console.log('ًں“ٹ Final files array:', files);
            setGeneratedFiles(files);
        } catch (err: any) {
            console.error('â‌Œ Failed to fetch generated files:', err);
            setFilesError('Failed to load generated files');
        } finally {
            setIsLoadingFiles(false);
        }
    };

    useEffect(() => {
        if (activeAction === 'documents' && projects.length > 0) {
            fetchGeneratedFiles();
        }
    }, [activeAction, projects]);

    // Click outside handler for user dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            const userSection = document.querySelector('.user-section');

            if (showUserDropdown && userSection && !userSection.contains(target)) {
                setShowUserDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showUserDropdown]);

    // Event handlers
    const handleDeleteProject = async (project: Project) => {
        setProjectToDelete(project);
        setShowDeleteModal(true);
    };

    const confirmDeleteProject = async () => {
        if (!projectToDelete) return;

        try {
            console.log('ًں—‘ï¸ڈ Deleting project:', projectToDelete.id, projectToDelete.title);
            await apiService.projects.delete(projectToDelete.id);

            // Remove project from local state
            setProjects(projects.filter(p => p.id !== projectToDelete.id));

            // ًں”„ Refetch notifications after successful deletion
            try {
                console.log('ًں”„ Refetching notifications after project deletion...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    console.log('ًں“¥ Notifications after deletion:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-deleted',
                            projectId: projectToDelete.id,
                            projectName: projectToDelete.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    console.log('âœ… Dispatched notification-update event');
                }
            } catch (notifError) {
                console.error('â‌Œ Failed to refetch notifications:', notifError);
            }

            showAlert({
                type: 'success',
                title: 'Success',
                message: 'Project deleted successfully'
            });
            setShowDeleteModal(false);
            setProjectToDelete(null);
        } catch (err: any) {
            const errorMessage = formatApiError(err);
            showAlert({
                type: 'error',
                title: 'Error',
                message: `Failed to delete project: ${errorMessage}`
            });
        }
    };

    const cancelDelete = () => {
        setShowDeleteModal(false);
        setProjectToDelete(null);
    };

    const handleEditProject = (project: Project) => {
        setEditingProject(project);
        setShowEditModal(true);
    };

    const handleUpdateProject = async (data: UpdateProjectData) => {
        if (!editingProject) return;

        try {
            const updatedProject = await apiService.projects.update(editingProject.id, data);
            setProjects(projects.map(p => p.id === editingProject.id ? updatedProject : p));
            setShowEditModal(false);
            setEditingProject(null);
            showAlert({
                type: 'success',
                title: 'Success',
                message: 'Project updated successfully'
            });
        } catch (err: any) {
            const errorMessage = formatApiError(err);
            showAlert({
                type: 'error',
                title: 'Error',
                message: `Failed to update project: ${errorMessage}`
            });
        }
    };

    const handleAddCode = (project: Project) => {
        setCodeProject(project);
        setShowCodeModal(true);
    };

    const handleCodeSubmit = async (payload: {
        projectId: string;
        codeName: string;
        fileName: string;
        language: 'auto-detect' | 'python' | 'java' | 'javascript' | 'typescript' | 'csharp' | 'go' | 'php' | 'cpp' | 'rust' | 'ruby' | 'swift' | 'kotlin' | 'scala' | 'dart' | 'r';
        version: string;
        codeText: string;
        file: File | null;
        files?: File[];
        zipFile?: File;
        githubUrl?: string;
    }) => {
        setIsCodeProcessing(true);
        setShowAnalysis(true);
        setCodeError(null);

        try {
            // ===== مسار ZIP / Folder Upload (Large Project Processing) =====
            if (payload.zipFile) {
                console.log('ًں“¦ ZIP detected â€” using folder-upload flow');

                // Step 1: رفع الـ ZIP
                const uploadResult = await UnifiedApiService.folderUpload(
                    payload.projectId,
                    payload.zipFile
                );
                console.log('âœ… Folder uploaded:', uploadResult);

                // استخدم الـ project_id اللي رجعه الـ backend (قد يكون مختلف عن payload.projectId)
                const actualProjectId = uploadResult.project_id || payload.projectId;
                console.log('ًں“Œ Using project_id for analysis:', actualProjectId);

                // Step 2: بدأ تحليل المشروع
                const analyzeResult = await UnifiedApiService.analyzeProject(actualProjectId);
                console.log('âœ… Project analysis started:', analyzeResult);

                const taskId = analyzeResult.task_id;

                // Step 3: انتظار اكتمال التحليل (polling)
                let analysisData: any = null;
                const maxAttempts = 40;
                const pollInterval = 3000;

                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    console.log(`ًں”„ Polling project analysis status (${attempt}/${maxAttempts})...`);
                    await new Promise(resolve => setTimeout(resolve, pollInterval));

                    try {
                        const statusData = await UnifiedApiService.getAnalyzeProjectStatus(actualProjectId);
                        console.log('ًں“ٹ Analysis status:', statusData.status);

                        if (statusData.status === 'COMPLETED' || statusData.status === 'COMPLETED_WITH_ERRORS') {
                            analysisData = statusData;
                            console.log('âœ… Project analysis completed!');
                            break;
                        } else if (statusData.status === 'FAILED') {
                            const reason = statusData.error_message || statusData.error || statusData.detail || '';
                            throw new Error('Project analysis failed on server' + (reason ? ': ' + reason : ''));
                        }
                        // IN_PROGRESS / PENDING - keep polling
                    } catch (pollError: any) {
                        // Only swallow 404 in first 2 attempts (analysis may not have started yet)
                        const is404 = (pollError?.response?.status === 404) || String(pollError?.message).includes('404');
                        if (is404 && attempt < 3) continue;
                        throw pollError;
                    }
                }

                if (!analysisData) {
                    throw new Error('Project analysis timed out. Please try again.');
                }

                // Step 4: جلب class diagram للمشروع
                const diagramData = await UnifiedApiService.getProjectClassDiagram(actualProjectId);
                console.log('âœ… Project class diagram fetched:', diagramData);

                // Close modal
                setShowCodeModal(false);
                setCodeProject(null);

                // Step 5: الانتقال لصفحة Class Diagram مع بيانات المشروع
                navigate('/diagram', {
                    state: {
                        projectId: actualProjectId,
                        codeName: payload.zipFile.name.replace('.zip', ''),
                        fileName: payload.zipFile.name,
                        isProjectDiagram: true,
                        analysisIds: analysisData.analysis_ids || [],
                        // تحويل format المشروع لـ format يفهمه ClassDiagramPage
                        diagram: convertProjectDiagramToDiagramFormat(diagramData.project_class_diagram),
                    }
                });

                showAlert({
                    type: 'success',
                    title: 'Success',
                    message: `Project analyzed successfully! Found ${diagramData.total_classes || 0} classes.`
                });

                return;
            }

            // ===== مسار GitHub Repo =====
            if (payload.githubUrl) {
                console.log('ًںگ™ GitHub URL detected â€” using folder-upload flow');
                // TODO: يمكن إضافة GitHub fetch logic هنا لاحقاً
                // حالياً نرسل للـ document generation مع الـ URL
            }

            // ===== مسار الملفات المحلية (Single/Multi file) =====
            console.log('âœ… Local files â€” using codefiles flow');
            if (payload.files && payload.files.length > 0) {
                await UnifiedApiService.uploadFilesWithProject({
                    files: payload.files,
                    project_id: payload.projectId,
                    language: payload.language,
                    version: payload.version,
                    codeName: payload.codeName,
                    githubUrl: payload.githubUrl,
                    zipFile: payload.zipFile
                });
            }

            console.log('âœ… Files uploaded successfully, navigating...');

            // Close modal
            setShowCodeModal(false);
            setCodeProject(null);

            // Navigate to document generation page
            navigate('/document-generation', {
                state: {
                    projectId: payload.projectId,
                    codeName: payload.codeName || payload.fileName,
                    fileName: payload.fileName,
                    language: payload.language,
                    codeText: payload.codeText || ' ', // space to avoid empty check
                }
            });

            showAlert({
                type: 'success',
                title: 'Success',
                message: 'Code uploaded successfully'
            });
        } catch (err: any) {
            const errorMessage = formatApiError(err);
            setCodeError(errorMessage);
            console.error('â‌Œ Error in handleCodeSubmit:', err);
        } finally {
            setIsCodeProcessing(false);
            setShowAnalysis(false);
        }
    };

    // Helper: تحويل project_class_diagram format لـ ClassDiagramPage format
    const convertProjectDiagramToDiagramFormat = (projectDiagram: any) => {
        if (!projectDiagram) return { classes: [], relationships: [] };

        const classes = (projectDiagram.classes || []).map((cls: any) => ({
            name: cls.name,
            is_abstract: cls.is_abstract || false,
            is_interface: cls.is_interface || false,
            attributes: (cls.attributes || []).map((attr: any) => ({
                name: attr.name,
                type: attr.type,
                visibility: attr.visibility || 'public',
            })),
            methods: (cls.methods || []).map((method: any) => {
                // parse signature: "+ methodName(param: Type): ReturnType"
                const sig = method.signature || method.name || '';
                return {
                    name: method.name,
                    visibility: method.visibility || 'public',
                    parameters: [],
                    return_type: extractReturnType(sig),
                    type: method.is_constructor ? 'constructor' : 'method',
                };
            }),
        }));

        const relationships = (projectDiagram.relationships || []).map((rel: any) => ({
            from: rel.from,
            to: rel.to,
            type: mapRelationshipType(rel.type),
            label: rel.label,
        }));

        return { classes, relationships };
    };

    const extractReturnType = (signature: string): string => {
        const match = signature.match(/\):\s*(.+)$/);
        return match ? match[1].trim() : 'void';
    };

    const mapRelationshipType = (type: string): string => {
        const mapping: Record<string, string> = {
            'inheritance': 'inheritance',
            'realization': 'implementation',
            'aggregation': 'aggregation',
            'composition': 'composition',
            'dependency': 'dependency',
            'association': 'association',
        };
        return mapping[type] || 'association';
    };

    const handleViewCodes = async (project: Project) => {
        setSelectedProject(project);
        setShowCodesModal(true);
        setIsLoadingCodes(true);

        try {
            const codes = await apiService.projects.getCodes(project.id);
            setProjectCodes(codes || []);
        } catch (err) {
            console.error('Failed to fetch codes:', err);
            setProjectCodes([]);
        } finally {
            setIsLoadingCodes(false);
        }
    };

    const handleViewProjectFiles = (project: Project) => {
        navigate(`/dashboard/projects/${project.id}/tree`);
    };


    const handleCreateProject = () => {
        setShowCreateProjectModal(true);
    };

    const handleCreateProjectSubmit = async (data: { title: string; description: string }) => {
        try {
            console.log('â‍• Creating project:', data.title);
            const newProject = await apiService.projects.create(data);
            setProjects([...projects, newProject]);

            // ًں”„ Refetch notifications after successful creation
            try {
                console.log('ًں”„ Refetching notifications after project creation...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    console.log('ًں“¥ Notifications after creation:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-created',
                            projectId: newProject.id,
                            projectName: newProject.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    console.log('âœ… Dispatched notification-update event for project creation');
                }
            } catch (notifError) {
                console.error('â‌Œ Failed to refetch notifications after creation:', notifError);
            }

            setShowCreateProjectModal(false);
            showAlert({
                type: 'success',
                title: 'Success',
                message: 'Project created successfully'
            });
        } catch (err: any) {
            const errorMessage = formatApiError(err);
            showAlert({
                type: 'error',
                title: 'Error',
                message: `Failed to create project: ${errorMessage}`
            });
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/auth');
    };

    const formatFileSize = (bytes: number): string => {
        if (!bytes) return 'â€”';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const handleDownloadFile = async (file: any) => {
        try {
            const token = localStorage.getItem('access_token') || '';
            const res = await fetch(`/api/analysis/download-generated-file/${file._id}/`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            if (!res.ok) throw new Error('Download failed');
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name || file.filename || 'file';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Download error:', err);
        }
    };

    const handleViewFile = async (file: any) => {
        try {
            const token = localStorage.getItem('access_token') || '';
            const res = await fetch(`/api/analysis/download-generated-file/${file._id}/`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            if (!res.ok) throw new Error('View failed');
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
            setTimeout(() => URL.revokeObjectURL(url), 10000);
        } catch (err) {
            console.error('View error:', err);
        }
    };

    // Render functions
    const renderMainContent = () => {
        if (activeAction === 'projects') {
            return (
                <div className="workspace-section">
                    {/* Hero Section */}
                    <div className="workspace-hero">
                        <div className="hero-glow-secondary" />
                        <div className="hero-content" style={{ alignItems: 'stretch' }}>
                            <div className="hero-header-container">
                                <h1 className="hero-title">
                                    {language === 'ar' ? 'مساحة المشاريع' : 'Projects Workspace'}
                                </h1>
                                <p className="hero-subtitle">
                                    {language === 'ar'
                                        ? 'نظم مشاريعك الجامعية وأرفق ملفات الكود البرمجية'
                                        : 'Organize your university projects and attach code artifacts'
                                    }
                                </p>
                            </div>

                            {/* Right column: spacer â†’ icons â†’ spacer â†’ button â†’ spacer */}
                            {/* Right column: spacer â†’ icons â†’ spacer â†’ button â†’ spacer */}
                            <div className="hero-right-col">
                                {/* Top spacer */}
                                <div className="hero-spacer hero-spacer-top" />

                                {/* Staircase icons */}
                                <div className="hero-feature-icons">
                                    {/* 1: Folder (amber) â€” bottom-left */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M1.5 7a1.2 1.2 0 0 1 1.2-1.2h7.5l1.5 1.8a.8.8 0 0 0 .6.3h11.5a1.2 1.2 0 0 1 1.2 1.2v11a1.2 1.2 0 0 1-1.2 1.2H2.7a1.2 1.2 0 0 1-1.2-1.2V7z" opacity="0.3" />
                                            <path d="M3 10.5a1.2 1.2 0 0 1 1.2-1.2h7.5l1.5 1.8a.8.8 0 0 0 .6.3h11.5a1.2 1.2 0 0 1 1.2 1.2v8a1.2 1.2 0 0 1-1.2 1.2H4.2A1.2 1.2 0 0 1 3 22.6v-12.1z" />
                                            <rect x="9" y="14.5" width="7" height="7" rx="0.8" opacity="0.45" />
                                            <line x1="11" y1="17" x2="14" y2="17" opacity="0.35" />
                                            <line x1="11" y1="19" x2="13.5" y2="19" opacity="0.35" />
                                        </svg>
                                    </div>
                                    {/* 2: UML Class (blue) â€” middle */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="0.5" y="0.5" width="10" height="9" rx="1.2" fill="rgba(56,189,248,0.08)" />
                                            <line x1="0.5" y1="3.5" x2="10.5" y2="3.5" />
                                            <text x="5.5" y="2.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">A</text>
                                            <line x1="2" y1="5.8" x2="9" y2="5.8" opacity="0.3" />
                                            <line x1="2" y1="7.5" x2="7.5" y2="7.5" opacity="0.3" />
                                            <rect x="17.5" y="0.5" width="10" height="9" rx="1.2" fill="rgba(56,189,248,0.08)" />
                                            <line x1="17.5" y1="3.5" x2="27.5" y2="3.5" />
                                            <text x="22.5" y="2.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">B</text>
                                            <line x1="19" y1="5.8" x2="26" y2="5.8" opacity="0.3" />
                                            <line x1="19" y1="7.5" x2="24" y2="7.5" opacity="0.3" />
                                            <rect x="7" y="16" width="14" height="11" rx="1.2" fill="rgba(56,189,248,0.08)" />
                                            <line x1="7" y1="19.5" x2="21" y2="19.5" />
                                            <text x="14" y="18.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">C</text>
                                            <line x1="9" y1="22" x2="19" y2="22" opacity="0.3" />
                                            <line x1="9" y1="24" x2="17" y2="24" opacity="0.3" />
                                            <line x1="5.5" y1="9.5" x2="10" y2="16" opacity="0.45" />
                                            <polygon points="10,16 9,14.5 10.8,14.8" fill="rgba(56,189,248,0.45)" stroke="none" />
                                            <line x1="22.5" y1="9.5" x2="18" y2="16" opacity="0.45" />
                                            <polygon points="18,16 19,14.5 17.2,14.8" fill="rgba(56,189,248,0.45)" stroke="none" />
                                            <line x1="10.5" y1="5" x2="17.5" y2="5" opacity="0.25" strokeDasharray="1.2 1" />
                                        </svg>
                                    </div>
                                    {/* 3: Explanation (green) â€” top-right */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="1" y="0.5" width="26" height="27" rx="2.5" fill="rgba(52,211,153,0.05)" />
                                            <rect x="1" y="0.5" width="26" height="6" rx="2.5" fill="rgba(52,211,153,0.1)" />
                                            <line x1="1" y1="6.5" x2="27" y2="6.5" opacity="0.3" />
                                            <circle cx="4.5" cy="3.5" r="0.8" fill="rgba(52,211,153,0.5)" stroke="none" />
                                            <circle cx="7.2" cy="3.5" r="0.8" fill="rgba(52,211,153,0.3)" stroke="none" />
                                            <line x1="10" y1="3.5" x2="22" y2="3.5" opacity="0.35" />
                                            <rect x="3.5" y="8.5" width="7" height="3.5" rx="0.8" fill="rgba(52,211,153,0.12)" stroke="rgba(52,211,153,0.3)" strokeWidth="0.7" />
                                            <text x="7" y="11.3" textAnchor="middle" fill="rgba(52,211,153,0.7)" fontSize="2.2" fontFamily="monospace" fontWeight="600" stroke="none">HIGH</text>
                                            <circle cx="3" cy="15" r="0.5" fill="rgba(52,211,153,0.45)" stroke="none" />
                                            <line x1="4.5" y1="15" x2="24" y2="15" opacity="0.2" />
                                            <circle cx="3" cy="17.5" r="0.5" fill="rgba(52,211,153,0.35)" stroke="none" />
                                            <line x1="4.5" y1="17.5" x2="21" y2="17.5" opacity="0.2" />
                                            <circle cx="3" cy="20" r="0.5" fill="rgba(52,211,153,0.35)" stroke="none" />
                                            <line x1="4.5" y1="20" x2="23" y2="20" opacity="0.2" />
                                            <line x1="3" y1="22" x2="24" y2="22" opacity="0.1" strokeDasharray="1.2 1" />
                                            <circle cx="3" cy="24" r="0.5" fill="rgba(52,211,153,0.3)" stroke="none" />
                                            <line x1="4.5" y1="24" x2="19" y2="24" opacity="0.15" />
                                            <circle cx="3" cy="26" r="0.5" fill="rgba(52,211,153,0.2)" stroke="none" />
                                            <line x1="4.5" y1="26" x2="22" y2="26" opacity="0.15" />
                                        </svg>
                                    </div>
                                </div>

                                {/* Middle spacer */}
                                <div className="hero-spacer hero-spacer-mid" />

                                <button
                                    onClick={handleCreateProject}
                                    className="btn-primary-gradient"
                                >
                                    <Plus size={20} />
                                    {language === 'ar' ? 'مشروع جديد' : 'New Project'}
                                </button>

                                {/* Bottom spacer */}
                                <div className="hero-spacer hero-spacer-bot" />
                            </div>
                        </div>
                    </div>

                    {/* Projects Table */}
                    <div className="projects-table-container">
                        {isLoadingProjects ? (
                            <div className="loading-state">
                                <div className="spinner"></div>
                                <p>{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</p>
                            </div>
                        ) : projectsError ? (
                            <div className="error-state">
                                <p>{projectsError}</p>
                                <button onClick={fetchProjects} className="btn-secondary">
                                    {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
                                </button>
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-icon">
                                    <Folder size={64} />
                                </div>
                                <h3>{language === 'ar' ? 'لا توجد مشاريع' : 'No projects yet'}</h3>
                                <p>
                                    {language === 'ar'
                                        ? 'ابدأ بإنشاء أول مشروع لك'
                                        : 'Create your first project to get started'
                                    }
                                </p>
                                <button
                                    onClick={handleCreateProject}
                                    className="btn-primary-gradient"
                                >
                                    <Plus size={20} />
                                    {language === 'ar' ? 'إنشاء أول مشروع' : 'Create First Project'}
                                </button>
                            </div>
                        ) : (
                            <div className="projects-table">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>{language === 'ar' ? 'العنوان' : 'Title'}</th>
                                            <th>{language === 'ar' ? 'الوصف' : 'Description'}</th>
                                            <th>{language === 'ar' ? 'المالك' : 'Owner'}</th>
                                            <th>{language === 'ar' ? 'تاريخ الإنشاء' : 'Created'}</th>
                                            <th>{language === 'ar' ? 'الإجراءات' : 'Actions'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {projects.map((project) => (
                                            <tr key={project.id} className="table-row">
                                                <td className="font-medium">{project.title}</td>
                                                <td className="text-muted">{project.description}</td>
                                                <td>{project.username || project.user}</td>
                                                <td>{new Date(project.created_at).toLocaleDateString('en-GB')}</td>
                                                <td>
                                                    <div className="actions">
                                                        <button
                                                            onClick={() => handleEditProject(project)}
                                                            className="action-btn action-edit"
                                                            title={language === 'ar' ? 'تعديل' : 'Edit'}
                                                        >
                                                            <Edit size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleAddCode(project)}
                                                            className="action-btn action-add"
                                                            title={language === 'ar' ? 'إضافة كود' : 'Add Code'}
                                                        >
                                                            <Plus size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleViewProjectFiles(project)}
                                                            className="action-btn action-view"
                                                            title={language === 'ar' ? 'عرض ملفات المشروع' : 'View Files'}
                                                        >
                                                            <Eye size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleDeleteProject(project)}
                                                            className="action-btn action-delete"
                                                            title={language === 'ar' ? 'حذف' : 'Delete'}
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        if (activeAction === 'documents') {
            // Group files by project
            const filesByProject = generatedFiles.reduce((acc: any, file) => {
                if (!acc[file.projectId]) {
                    acc[file.projectId] = { projectName: file.projectName, files: [] };
                }
                acc[file.projectId].files.push(file);
                return acc;
            }, {});

            return (
                <div className="documents-section">
                    <h1 className="section-title">
                        {language === 'ar' ? 'الملفات المُنشأة' : 'Generated Files'}
                    </h1>
                    <p className="section-subtitle">
                        {language === 'ar'
                            ? 'عرض وتنزيل جميع الملفات التي تم إنشاؤها من مشاريعك'
                            : 'View and download all files generated from your projects'
                        }
                    </p>

                    {isLoadingFiles ? (
                        <div className="loading-state">
                            <div className="spinner" />
                            <p>{language === 'ar' ? 'جاري تحميل الملفات...' : 'Loading files...'}</p>
                        </div>
                    ) : filesError ? (
                        <div className="error-state">
                            <p>{filesError}</p>
                            <button onClick={fetchGeneratedFiles} className="btn-secondary">
                                {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
                            </button>
                        </div>
                    ) : Object.keys(filesByProject).length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-icon"><Download size={64} /></div>
                            <h3>{language === 'ar' ? 'لا توجد ملفات مُنشأة' : 'No generated files yet'}</h3>
                            <p>{language === 'ar' ? 'ابدأ بإنشاء بعض الملفات من مشاريعك' : 'Generate some files from your projects to see them here'}</p>
                        </div>
                    ) : (
                        <div className="files-container">
                            {Object.entries(filesByProject).map(([projectId, projectData]: [string, any]) => (
                                <DashProjectSection
                                    key={projectId}
                                    projectName={projectData.projectName}
                                    files={projectData.files}
                                    onView={handleViewFile}
                                    onDownload={handleDownloadFile}
                                    isDark={isDarkMode}
                                    lang={language}
                                />
                            ))}
                        </div>
                    )}
                </div>
            );
        }

        return null;
    };

    return (
        <div className={`dashboard ${isDarkMode ? 'dark' : 'light'} ${language === 'ar' ? 'rtl' : 'ltr'} ${isSidebarOpen ? 'sidebar-open' : ''}`}>
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="sidebar-toggle"
                    >
                        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                    <div className="logo-section">
                        <Home size={32} className="logo-icon" />
                        <span className="logo-text">AutoTestDocGen</span>
                    </div>
                </div>

                <div className="header-right">
                    {/* Language Toggle */}
                    <button
                        onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
                        className="unified-theme-toggle"
                        style={{ width: '44px', fontSize: '11px', fontWeight: 700, letterSpacing: '0.03em' }}
                    >
                        {language === 'en' ? 'AR' : 'EN'}
                    </button>

                    {/* Theme Toggle */}
                    <button
                        onClick={() => setIsDarkMode(!isDarkMode)}
                        className="unified-theme-toggle"
                    >
                        {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
                    </button>

                    {/* Notifications */}
                    <div className="notification-container unified-theme-toggle" style={{ cursor: 'default', overflow: 'visible' }}>
                        <NotificationBell userId={user?.id?.toString()} />
                    </div>

                    {/* User Avatar & Dropdown */}
                    <div className="user-section">
                        <button
                            onClick={() => {
                                setShowUserDropdown(!showUserDropdown);
                            }}
                            className="unified-theme-toggle"
                        >
                            <div className="user-avatar">
                                {user?.username?.charAt(0).toUpperCase() || 'U'}
                            </div>
                        </button>

                        {showUserDropdown && (
                            <div className="user-dropdown show">
                                <div className="dropdown-header">
                                    <div className="user-info">
                                        <div className="user-avatar">
                                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                                        </div>
                                        <div>
                                            <div className="user-name">{user?.username || 'User'}</div>
                                            <div className="user-email">{user?.email || 'user@example.com'}</div>
                                        </div>
                                    </div>
                                </div>
                                <div className="dropdown-items">
                                    <button
                                        onClick={() => {
                                            setShowProfileModal(true);
                                            setShowUserDropdown(false);
                                        }}
                                        className="dropdown-item"
                                    >
                                        <User size={16} />
                                        {language === 'ar' ? 'الملف الشخصي' : 'Profile'}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowChangePasswordModal(true);
                                            setShowUserDropdown(false);
                                        }}
                                        className="dropdown-item"
                                    >
                                        <Lock size={16} />
                                        {language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowSecurityModal(true);
                                            setShowUserDropdown(false);
                                        }}
                                        className="dropdown-item"
                                    >
                                        <ShieldAlert size={16} />
                                        {language === 'ar' ? 'الأمان' : 'Security'}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowHelpModal(true);
                                            setShowUserDropdown(false);
                                        }}
                                        className="dropdown-item"
                                    >
                                        <HelpCircle size={16} />
                                        {language === 'ar' ? 'المساعدة' : 'Help'}
                                    </button>
                                    <div className="dropdown-divider"></div>
                                    <button
                                        onClick={handleLogout}
                                        className="dropdown-item logout-item"
                                    >
                                        <LogOut size={16} />
                                        {language === 'ar' ? 'تسجيل الخروج' : 'Logout'}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Sidebar */}
            <aside className={`dashboard-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
                <nav className="sidebar-nav">
                    <button
                        onClick={() => setActiveAction('projects')}
                        className={`nav-item ${activeAction === 'projects' ? 'active' : ''}`}
                    >
                        <Folder size={20} />
                        <span>{language === 'ar' ? 'المشاريع' : 'Projects'}</span>
                    </button>
                    <button
                        onClick={() => setActiveAction('documents')}
                        className={`nav-item ${activeAction === 'documents' ? 'active' : ''}`}
                    >
                        <Download size={20} />
                        <span>{language === 'ar' ? 'الملفات المُنشأة' : 'Generated Files'}</span>
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <div className="user-profile">
                        <div className="user-avatar">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="user-details">
                            <div className="user-name">{user?.username || 'User'}</div>
                            <div className="user-role">{language === 'ar' ? 'طالب' : 'Student'}</div>
                        </div>
                    </div>
                    <div className="sidebar-actions">
                        <button
                            onClick={() => setShowSecurityModal(true)}
                            className="sidebar-action-btn"
                            title={language === 'ar' ? 'الإعدادات' : 'Settings'}
                        >
                            <Lock size={16} />
                            <span>{language === 'ar' ? 'الإعدادات' : 'Settings'}</span>
                        </button>
                        <button
                            onClick={handleLogout}
                            className="sidebar-action-btn logout-btn"
                            title={language === 'ar' ? 'تسجيل الخروج' : 'Log Out'}
                        >
                            <LogOut size={16} />
                            <span>{language === 'ar' ? 'تسجيل الخروج' : 'Log Out'}</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className={`dashboard-main ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
                <div className="main-content">
                    {renderMainContent()}
                </div>
            </main>

            {/* Modals */}
            {showEditModal && editingProject && (
                <EditProjectForm
                    project={editingProject}
                    onSubmit={handleUpdateProject}
                    onClose={() => {
                        setShowEditModal(false);
                        setEditingProject(null);
                    }}
                    isLoading={false}
                    apiError={null}
                    isDark={isDarkMode}
                    lang={language}
                />
            )}

            {showCreateProjectModal && (
                <CreateProjectForm
                    onSubmit={handleCreateProjectSubmit}
                    onClose={() => setShowCreateProjectModal(false)}
                    isLoading={false}
                    apiError={null}
                    isDark={isDarkMode}
                    lang={language}
                />
            )}

            {showCodeModal && codeProject && (
                <CodeUploadForm
                    project={codeProject}
                    onGenerateDiagram={handleCodeSubmit}
                    onClose={() => {
                        setShowCodeModal(false);
                        setCodeProject(null);
                    }}
                    isProcessing={isCodeProcessing}
                    apiError={codeError}
                />
            )}

            {showAnalysis && (
                <AnalysisOverlay
                    message={codeError || 'Processing code, please wait...'}
                />
            )}


            {showCodesModal && selectedProject && (
                <ProjectCodesModal
                    isOpen={showCodesModal}
                    onClose={() => setShowCodesModal(false)}
                    projectId={selectedProject.id}
                    projectName={selectedProject.title}
                    codes={projectCodes}
                    isLoading={isLoadingCodes}
                />
            )}

            {showDocumentsModal && selectedProject && (
                <ProjectDocumentsModal
                    isOpen={showDocumentsModal}
                    onClose={() => setShowDocumentsModal(false)}
                    projectId={selectedProject.id}
                    projectName={selectedProject.title}
                    documents={projectDocuments}
                    isLoading={isLoadingDocuments}
                />
            )}

            {showProfileModal && (
                <ProfileModal
                    isOpen={showProfileModal}
                    onClose={() => setShowProfileModal(false)}
                    user={user}
                    onSave={(data: any) => {
                        console.log('Profile updated:', data);
                        setShowProfileModal(false);
                    }}
                    isLoading={false}
                />
            )}

            {showChangePasswordModal && (
                <ChangePasswordModal
                    isOpen={showChangePasswordModal}
                    onClose={() => setShowChangePasswordModal(false)}
                    isLoading={false}
                />
            )}

            {showSecurityModal && (
                <SecurityModal
                    isOpen={showSecurityModal}
                    onClose={() => setShowSecurityModal(false)}
                    language={language}
                />
            )}

            {showHelpModal && (
                <HelpModal
                    isOpen={showHelpModal}
                    onClose={() => setShowHelpModal(false)}
                    language={language}
                />
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="modal-overlay" onClick={cancelDelete}>
                    <div className="modal-content delete-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="delete-modal-header">
                            <div className="delete-icon">
                                <Trash2 size={48} />
                            </div>
                            <h3>
                                {language === 'ar' ? 'تأكيد الحذف' : 'Confirm Delete'}
                            </h3>
                        </div>

                        <div className="delete-modal-body">
                            <p>
                                {language === 'ar'
                                    ? `هل أنت متأكد من حذف المشروع "${projectToDelete?.title}"؟ لا يمكن التراجع عن هذا الإجراء.`
                                    : `Are you sure you want to delete the project "${projectToDelete?.title}"? This action cannot be undone.`
                                }
                            </p>
                        </div>

                        <div className="delete-modal-actions">
                            <button
                                type="button"
                                className="btn-secondary"
                                onClick={cancelDelete}
                            >
                                {language === 'ar' ? 'إلغاء' : 'Cancel'}
                            </button>
                            <button
                                type="button"
                                className="btn-danger"
                                onClick={confirmDeleteProject}
                            >
                                {language === 'ar' ? 'حذف' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {AlertComponent}

            {/* Chat Widget */}
            <ChatWidget language={language} />
        </div>
    );
};

export default Dashboard;
