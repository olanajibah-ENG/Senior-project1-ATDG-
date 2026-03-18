import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LogOut, Home, User, Lock,
    Globe, HelpCircle, Sun, Moon, Plus,
    Folder, FileDown, ShieldAlert,
    Menu, X, Edit, Trash2, Download, Eye
} from 'lucide-react';

import { type Project, type PaginatedResponse, type UpdateProjectData, formatApiError } from './services/api.service';
import apiService from './services/api.service';
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

// Edit Project Form Component
const EditProjectForm: React.FC<{
    project: Project;
    onSubmit: (data: UpdateProjectData) => void;
    onClose: () => void;
    isLoading: boolean;
    apiError: string | null;
}> = ({ project, onSubmit, onClose, isLoading, apiError }) => {
    const [title, setTitle] = useState(project.title);
    const [description, setDescription] = useState(project.description);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, description });
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2 className="modal-title">Edit Project</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                        />
                    </div>
                    {apiError && <div className="error-message">{apiError}</div>}
                    <div className="modal-actions">
                        <button type="button" onClick={onClose} disabled={isLoading}>
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading}>
                            {isLoading ? 'Saving...' : 'Save Changes'}
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
}> = ({ onSubmit, onClose, isLoading, apiError }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, description });
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2 className="modal-title">Create New Project</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                        />
                    </div>
                    {apiError && <div className="error-message">{apiError}</div>}
                    <div className="modal-actions">
                        <button type="button" onClick={onClose} disabled={isLoading}>
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading}>
                            {isLoading ? 'Creating...' : 'Create Project'}
                        </button>
                    </div>
                </form>
            </div>
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

            console.log('🔄 Fetching projects...');
            const response: PaginatedResponse<Project> = await apiService.projects.list();
            console.log('📊 API Response:', response);

            if (response && response.results && Array.isArray(response.results)) {
                console.log('✅ Projects loaded:', response.results.length, 'projects');
                setProjects(response.results);
            } else if (response && Array.isArray(response)) {
                console.log('✅ Projects loaded (direct array):', response.length, 'projects');
                setProjects(response);
            } else {
                console.error("❌ API response missing 'results' array or invalid structure:", response);
                setProjectsError('Invalid data structure received from server.');
                setProjects([]);
            }
        } catch (err: any) {
            console.error('❌ Failed to fetch projects:', err);

            if (err.response?.status === 401) {
                console.log('🔐 Authentication failed, clearing tokens and redirecting...');
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

    // Fetch generated files
    const fetchGeneratedFiles = async () => {
        console.log('🔄 Fetching generated files...');
        setIsLoadingFiles(true);
        setFilesError(null);
        try {
            const files: any[] = [];
            console.log('📁 Available projects:', projects.length);

            // Fetch documentation for each project
            for (const project of projects) {
                try {
                    console.log(`📄 Fetching docs for project ${project.id}: ${project.title}`);
                    const docs = await apiService.projects.getDocs(project.id);
                    console.log(`📋 Docs received for project ${project.id}:`, docs);

                    if (docs && Array.isArray(docs)) {
                        docs.forEach((doc: any) => {
                            files.push({
                                ...doc,
                                projectName: project.title,
                                projectId: project.id,
                                type: doc.file_name?.endsWith('.pdf') ? 'pdf' : 'markdown'
                            });
                        });
                    }
                } catch (err) {
                    console.warn(`❌ Failed to fetch docs for project ${project.id}:`, err);
                }
            }
            console.log('📊 Final files array:', files);
            setGeneratedFiles(files);
        } catch (err: any) {
            console.error('❌ Failed to fetch generated files:', err);
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

    // Event handlers
    const handleDeleteProject = async (project: Project) => {
        setProjectToDelete(project);
        setShowDeleteModal(true);
    };

    const confirmDeleteProject = async () => {
        if (!projectToDelete) return;

        try {
            console.log('🗑️ Deleting project:', projectToDelete.id, projectToDelete.title);
            await apiService.projects.delete(projectToDelete.id);

            // Remove project from local state
            setProjects(projects.filter(p => p.id !== projectToDelete.id));

            // 🔄 Refetch notifications after successful deletion
            try {
                console.log('🔄 Refetching notifications after project deletion...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    console.log('📥 Notifications after deletion:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-deleted',
                            projectId: projectToDelete.id,
                            projectName: projectToDelete.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    console.log('✅ Dispatched notification-update event');
                }
            } catch (notifError) {
                console.error('❌ Failed to refetch notifications:', notifError);
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
        language: 'python' | 'java';
        version: string;
        codeText: string;
        file: File | null;
    }) => {
        setIsCodeProcessing(true);
        setShowAnalysis(true);
        setCodeError(null);

        try {
            console.log('✅ Code submitted, closing modal and navigating...');

            // Close modal immediately
            setShowCodeModal(false);
            setCodeProject(null);

            // Navigate directly to document generation page
            navigate('/document-generation', {
                state: {
                    projectId: payload.projectId,
                    codeName: payload.codeName || payload.fileName,
                    fileName: payload.fileName,
                    language: payload.language,
                    codeText: payload.codeText
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
            console.error('❌ Error in handleCodeSubmit:', err);
        } finally {
            setIsCodeProcessing(false);
            setShowAnalysis(false);
        }
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

    const handleViewDocuments = async (project: Project) => {
        setSelectedProject(project);
        setShowDocumentsModal(true);
        setIsLoadingDocuments(true);

        try {
            const documents = await apiService.projects.getDocs(project.id);
            setProjectDocuments(documents || []);
        } catch (err) {
            console.error('Failed to fetch documents:', err);
            setProjectDocuments([]);
        } finally {
            setIsLoadingDocuments(false);
        }
    };


    const handleCreateProject = () => {
        setShowCreateProjectModal(true);
    };

    const handleCreateProjectSubmit = async (data: { title: string; description: string }) => {
        try {
            console.log('➕ Creating project:', data.title);
            const newProject = await apiService.projects.create(data);
            setProjects([...projects, newProject]);

            // 🔄 Refetch notifications after successful creation
            try {
                console.log('🔄 Refetching notifications after project creation...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    console.log('📥 Notifications after creation:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-created',
                            projectId: newProject.id,
                            projectName: newProject.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    console.log('✅ Dispatched notification-update event for project creation');
                }
            } catch (notifError) {
                console.error('❌ Failed to refetch notifications after creation:', notifError);
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

    // Render functions
    const renderMainContent = () => {
        if (activeAction === 'projects') {
            return (
                <div className="workspace-section">
                    {/* Hero Section */}
                    <div className="workspace-hero">
                        <div className="hero-content">
                            <h1 className="hero-title">
                                {language === 'ar' ? 'مساحة المشاريع' : 'Projects Workspace'}
                            </h1>
                            <p className="hero-subtitle">
                                {language === 'ar'
                                    ? 'نظم مشاريعك الجامعية وأرفق ملفات الكود البرمجية'
                                    : 'Organize your university projects and attach code artifacts'
                                }
                            </p>
                            <button
                                onClick={handleCreateProject}
                                className="btn-primary-gradient"
                            >
                                <Plus size={20} />
                                {language === 'ar' ? 'مشروع جديد' : 'New Project'}
                            </button>
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
                                                <td>{new Date(project.created_at).toLocaleDateString()}</td>
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
                                                            onClick={() => handleViewCodes(project)}
                                                            className="action-btn action-view"
                                                            title={language === 'ar' ? 'عرض الأكواد' : 'View Code'}
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
            console.log('📄 Rendering documents section');
            console.log('📁 Generated files:', generatedFiles);
            console.log('⏳ Is loading files:', isLoadingFiles);
            console.log('❌ Files error:', filesError);

            // Group files by project
            const filesByProject = generatedFiles.reduce((acc: any, file) => {
                if (!acc[file.projectId]) {
                    acc[file.projectId] = {
                        projectName: file.projectName,
                        files: []
                    };
                }
                acc[file.projectId].files.push(file);
                return acc;
            }, {});

            console.log('📊 Files by project:', filesByProject);

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
                            <div className="spinner"></div>
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
                            <div className="empty-icon">
                                <Download size={64} />
                            </div>
                            <h3>{language === 'ar' ? 'لا توجد ملفات مُنشأة' : 'No generated files yet'}</h3>
                            <p>
                                {language === 'ar'
                                    ? 'ابدأ بإنشاء بعض الملفات من مشاريعك'
                                    : 'Generate some files from your projects to see them here'
                                }
                            </p>
                        </div>
                    ) : (
                        <div className="files-container">
                            {Object.entries(filesByProject).map(([projectId, projectData]: [string, any]) => (
                                <div key={projectId} className="project-files-card">
                                    <div className="project-header">
                                        <h3 className="project-name">{projectData.projectName}</h3>
                                        <span className="file-count">
                                            {projectData.files.length} {language === 'ar' ? 'ملف' : 'files'}
                                        </span>
                                    </div>
                                    <div className="files-list">
                                        {projectData.files.map((file: any, index: number) => (
                                            <div key={index} className="file-item">
                                                <div className="file-info">
                                                    <div className="file-icon">
                                                        {file.type === 'pdf' ? (
                                                            <span className="pdf-icon">PDF</span>
                                                        ) : (
                                                            <span className="md-icon">MD</span>
                                                        )}
                                                    </div>
                                                    <div className="file-details">
                                                        <h4 className="file-name">{file.file_name || file.name}</h4>
                                                        <p className="file-description">
                                                            {file.description || `${language === 'ar' ? 'ملف' : 'File'} ${index + 1}`}
                                                        </p>
                                                        <span className="file-date">
                                                            {new Date(file.created_at).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="file-actions">
                                                    <button
                                                        className="action-btn action-view"
                                                        title={language === 'ar' ? 'عرض' : 'View'}
                                                    >
                                                        <Eye size={16} />
                                                    </button>
                                                    <button
                                                        className="action-btn action-download"
                                                        title={language === 'ar' ? 'تحميل' : 'Download'}
                                                    >
                                                        <Download size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
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
                        className="toggle-btn language-toggle"
                    >
                        <Globe size={16} />
                        {language === 'en' ? 'AR' : 'EN'}
                    </button>

                    {/* Theme Toggle */}
                    <button
                        onClick={() => setIsDarkMode(!isDarkMode)}
                        className="toggle-btn theme-toggle"
                    >
                        {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
                    </button>

                    {/* Notifications */}
                    <div className="notification-container">
                        <NotificationBell userId={user?.id?.toString()} />
                    </div>

                    {/* User Avatar & Dropdown */}
                    <div className="user-section">
                        <button
                            onClick={() => {
                                console.log('👤 User avatar clicked, current state:', showUserDropdown);
                                setShowUserDropdown(!showUserDropdown);
                                console.log('👤 User dropdown state changed to:', !showUserDropdown);
                            }}
                            className="user-avatar-btn"
                        >
                            <div className="user-avatar">
                                {user?.username?.charAt(0).toUpperCase() || 'U'}
                            </div>
                        </button>

                        {showUserDropdown && (
                            <div className="user-dropdown">
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
                />
            )}

            {showCreateProjectModal && (
                <CreateProjectForm
                    onSubmit={handleCreateProjectSubmit}
                    onClose={() => setShowCreateProjectModal(false)}
                    isLoading={false}
                    apiError={null}
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
