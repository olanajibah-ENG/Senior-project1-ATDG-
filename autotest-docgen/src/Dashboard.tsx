import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LogOut, Home, User, Lock,
    HelpCircle, Sun, Moon, Plus,
    Folder, ShieldAlert, Code,
    Menu, X, Edit, Trash2, Download, Eye, FileText,
    AlertCircle, CheckCircle, GitCompare
} from 'lucide-react';

import { type Project, type PaginatedResponse, type UpdateProjectData, formatApiError } from './services/api.service';
import logger from './utils/logger';
import apiService from './services/api.service';
import UnifiedApiService from './services/unifiedApiService';
import apiClient from './services/apiClient';
import { AuthContext } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import CodeUploadForm from './components/ProjectCustomizationModal/CodeUploadForm';
import AnalysisOverlay from './components/ProjectCustomizationModal/AnalysisOverlay';
import { useAlert } from './components/Alert/useAlert';
import NotificationBell from './components/NotificationBell';
import ChatWidget from './components/ChatWidget/ChatWidget';
import ProfileModal from './components/ProfileModal/ProfileModal';
import ChangePasswordModal from './components/ChangePasswordModal/ChangePasswordModal';
import SecurityModal from './components/SecurityModal/SecurityModal';
import HelpModal from './components/HelpModal/HelpModal';
import {
  SimpleConflictSelector,
  CodeVsCode,
  CodeVsDoc,
  FullAnalysis,
} from './components/ConflictDetection';
import type { ConflictType } from './components/ConflictDetection';
import './Dashboard-Modern.css';
import './Dashboard.css';

import EditProjectForm from './components/Dashboard/EditProjectForm';
import CreateProjectForm from './components/Dashboard/CreateProjectForm';
import DashProjectSection from './components/Dashboard/DashProjectSection';

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const { user, logout } = useContext(AuthContext);
    const { language, setLanguage } = useLanguage();
    const { showAlert, AlertComponent } = useAlert();

    // State management
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectsError, setProjectsError] = useState<string | null>(null);
    const [isLoadingProjects, setIsLoadingProjects] = useState(true);
    const [activeAction, setActiveAction] = useState<'projects' | 'documents' | 'conflict'>('projects');
    const [activeConflictType, setActiveConflictType] = useState<ConflictType | null>(null);
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
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
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

            logger.log('🔄 Fetching projects...');
            const response: PaginatedResponse<Project> = await apiService.projects.list();
            logger.log('📊 API Response:', response);

            if (response && response.results && Array.isArray(response.results)) {
                logger.log('✅ Projects loaded:', response.results.length, 'projects');
                setProjects(response.results);
            } else if (response && Array.isArray(response)) {
                logger.log('✅ Projects loaded (direct array):', response.length, 'projects');
                setProjects(response);
            } else {
                logger.error("❌ API response missing 'results' array or invalid structure:", response);
                setProjectsError('Invalid data structure received from server.');
                setProjects([]);
            }
        } catch (err: any) {
            logger.error('❌ Failed to fetch projects:', err);

            if (err.response?.status === 401) {
                logger.log('🔒 Authentication failed, clearing tokens and redirecting...');
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

    // Fetch generated files — fetch all then filter by user's projects
    const fetchGeneratedFiles = async () => {
        logger.log('🔄 Fetching generated files...');
        setIsLoadingFiles(true);
        setFilesError(null);
        try {
            // Fetch all generated files (backend filters by authenticated user automatically)
            const res = await apiClient.get('/api/analysis/generated-files/');
            const data = res.data;
            const raw: any[] = Array.isArray(data) ? data : data.files || data.results || [];

            // Build a lookup of user's project IDs → project title
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

            logger.log('📊 Final files array:', files);
            setGeneratedFiles(files);
        } catch (err: any) {
            logger.error('❌ Failed to fetch generated files:', err);
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
            logger.log('🗑️ Deleting project:', projectToDelete.id, projectToDelete.title);
            await apiService.projects.delete(projectToDelete.id);

            // Remove project from local state
            setProjects(projects.filter(p => p.id !== projectToDelete.id));

            // 🔄 Refetch notifications after successful deletion
            try {
                logger.log('🔄 Refetching notifications after project deletion...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    logger.log('📥 Notifications after deletion:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-deleted',
                            projectId: projectToDelete.id,
                            projectName: projectToDelete.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    logger.log('✅ Dispatched notification-update event');
                }
            } catch (notifError) {
                logger.error('❌ Failed to refetch notifications:', notifError);
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
                logger.log('📦 ZIP detected — using folder-upload flow');

                // Step 1: رفع الـ ZIP
                const uploadResult = await UnifiedApiService.folderUpload(
                    payload.projectId,
                    payload.zipFile
                );
                logger.log('✅ Folder uploaded:', uploadResult);

                // استخدم الـ project_id اللي رجعه الـ backend (قد يكون مختلف عن payload.projectId)
                const actualProjectId = uploadResult.project_id || payload.projectId;
                logger.log('📌 Using project_id for analysis:', actualProjectId);

                // Step 2: Wait for files to reach AI service (UPM -> Celery -> AI is async)
                const uploadedFileCount = uploadResult.file_count ?? 1;
                logger.log('Waiting for ' + uploadedFileCount + ' file(s) to reach AI service...');
                await UnifiedApiService.waitForFilesInAI(actualProjectId, uploadedFileCount);

                // Step 3: Start project analysis
                const analyzeResult = await UnifiedApiService.analyzeProject(actualProjectId);
                logger.log('✅ Project analysis started:', analyzeResult);

                const taskId = analyzeResult.task_id;

                // Step 4: انتظار اكتمال التحليل (polling)
                let analysisData: any = null;
                const maxAttempts = 40;
                const pollInterval = 3000;

                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    logger.log(`🔄 Polling project analysis status (${attempt}/${maxAttempts})...`);
                    await new Promise(resolve => setTimeout(resolve, pollInterval));

                    try {
                        const statusData = await UnifiedApiService.getAnalyzeProjectStatus(actualProjectId);
                        logger.log('📊 Analysis status:', statusData.status);

                        if (statusData.status === 'COMPLETED' || statusData.status === 'COMPLETED_WITH_ERRORS') {
                            analysisData = statusData;
                            logger.log('✅ Project analysis completed!');
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
                logger.log('✅ Project class diagram fetched:', diagramData);

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

            // ===== GitHub Repo =====
            if (payload.githubUrl) {
                logger.log('→ GitHub URL detected → using project analysis flow like ZIP');
                
                // Step 1: GitHub is already connected, get project analysis
                const analyzeResult = await UnifiedApiService.analyzeProject(payload.projectId);
                logger.log('→ GitHub project analysis started:', analyzeResult);

                const taskId = analyzeResult.task_id;

                // Step 2: Wait for analysis completion (polling)
                let analysisData: any = null;
                const maxAttempts = 40;
                const pollInterval = 3000;

                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    logger.log(`→ Polling GitHub project analysis status (${attempt}/${maxAttempts})...`);
                    await new Promise(resolve => setTimeout(resolve, pollInterval));

                    try {
                        const statusData = await UnifiedApiService.getAnalyzeProjectStatus(payload.projectId);
                        logger.log('→ GitHub analysis status:', statusData.status);

                        if (statusData.status === 'COMPLETED' || statusData.status === 'COMPLETED_WITH_ERRORS') {
                            analysisData = statusData;
                            logger.log('→ GitHub project analysis completed!');
                            break;
                        } else if (statusData.status === 'FAILED') {
                            const reason = statusData.error_message || statusData.error || statusData.detail || '';
                            throw new Error('GitHub project analysis failed on server' + (reason ? ': ' + reason : ''));
                        }
                        // IN_PROGRESS / PENDING - keep polling
                    } catch (pollError: any) {
                        const is404 = (pollError?.response?.status === 404) || String(pollError?.message).includes('404');
                        if (is404 && attempt < 3) continue;
                        throw pollError;
                    }
                }

                if (!analysisData) {
                    throw new Error('GitHub project analysis timed out. Please try again.');
                }

                // Step 3: Get project class diagram
                const diagramData = await UnifiedApiService.getProjectClassDiagram(payload.projectId);
                logger.log('→ GitHub project class diagram fetched:', diagramData);

                // Close modal
                setShowCodeModal(false);
                setCodeProject(null);

                // Step 4: Navigate to Class Diagram page with project data (same as ZIP)
                navigate('/diagram', {
                    state: {
                        projectId: payload.projectId,
                        codeName: payload.codeName || 'GitHub Repository',
                        fileName: payload.fileName || 'GitHub Repository',
                        isProjectDiagram: true,
                        analysisIds: analysisData.analysis_ids || [],
                        diagram: convertProjectDiagramToDiagramFormat(diagramData.project_class_diagram),
                    }
                });

                showAlert({
                    type: 'success',
                    title: 'Success',
                    message: `GitHub repository analyzed successfully! Found ${diagramData.total_classes || 0} classes.`
                });

                return;
            }

            // ===== Multi-file upload (treat as project) =====
            if (payload.files && payload.files.length > 1) {
                logger.log('→ Multiple files detected → using project analysis flow like ZIP');
                
                // Step 1: Upload files as project
                await UnifiedApiService.uploadFilesWithProject({
                    files: payload.files,
                    project_id: payload.projectId,
                    language: payload.language,
                    version: payload.version,
                    codeName: payload.codeName,
                    githubUrl: payload.githubUrl,
                    zipFile: payload.zipFile
                });

                // Step 2: Start project analysis
                const analyzeResult = await UnifiedApiService.analyzeProject(payload.projectId);
                logger.log('→ Project analysis started:', analyzeResult);

                const taskId = analyzeResult.task_id;

                // Step 3: Poll for analysis completion
                let analysisData: any = null;
                const maxAttempts = 40;
                const pollInterval = 3000;

                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    logger.log(`→ Polling project analysis status (${attempt}/${maxAttempts})...`);
                    await new Promise(resolve => setTimeout(resolve, pollInterval));

                    try {
                        const statusData = await UnifiedApiService.getAnalyzeProjectStatus(payload.projectId);
                        logger.log('→ Analysis status:', statusData.status);

                        if (statusData.status === 'COMPLETED' || statusData.status === 'COMPLETED_WITH_ERRORS') {
                            analysisData = statusData;
                            logger.log('→ Project analysis completed!');
                            break;
                        } else if (statusData.status === 'FAILED') {
                            const reason = statusData.error_message || statusData.error || statusData.detail || '';
                            throw new Error('Project analysis failed on server' + (reason ? ': ' + reason : ''));
                        }
                    } catch (pollError: any) {
                        const is404 = (pollError?.response?.status === 404) || String(pollError?.message).includes('404');
                        if (is404 && attempt < 3) continue;
                        throw pollError;
                    }
                }

                if (!analysisData) {
                    throw new Error('Project analysis timed out. Please try again.');
                }

                // Step 4: Get project class diagram
                const diagramData = await UnifiedApiService.getProjectClassDiagram(payload.projectId);
                logger.log('→ Project class diagram fetched:', diagramData);

                // Close modal
                setShowCodeModal(false);
                setCodeProject(null);

                // Step 5: Navigate to Class Diagram page
                navigate('/diagram', {
                    state: {
                        projectId: payload.projectId,
                        codeName: payload.codeName || 'Multi-file Project',
                        fileName: payload.fileName || 'Multi-file Project',
                        isProjectDiagram: true,
                        analysisIds: analysisData.analysis_ids || [],
                        diagram: convertProjectDiagramToDiagramFormat(diagramData.project_class_diagram),
                    }
                });

                showAlert({
                    type: 'success',
                    title: 'Success',
                    message: `Multi-file project analyzed successfully! Found ${diagramData.total_classes || 0} classes.`
                });

                return;
            }

            // ===== Single file upload (treat as project) =====
            if (payload.files && payload.files.length === 1) {
                logger.log('→ Single file detected → using project analysis flow like ZIP');
                
                // Step 1: Upload file as project
                await UnifiedApiService.uploadFilesWithProject({
                    files: payload.files,
                    project_id: payload.projectId,
                    language: payload.language,
                    version: payload.version,
                    codeName: payload.codeName,
                    githubUrl: payload.githubUrl,
                    zipFile: payload.zipFile
                });

                // Step 2: Start project analysis
                const analyzeResult = await UnifiedApiService.analyzeProject(payload.projectId);
                logger.log('→ Project analysis started:', analyzeResult);

                const taskId = analyzeResult.task_id;

                // Step 3: Poll for analysis completion
                let analysisData: any = null;
                const maxAttempts = 40;
                const pollInterval = 3000;

                for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                    logger.log(`→ Polling project analysis status (${attempt}/${maxAttempts})...`);
                    await new Promise(resolve => setTimeout(resolve, pollInterval));

                    try {
                        const statusData = await UnifiedApiService.getAnalyzeProjectStatus(payload.projectId);
                        logger.log('→ Analysis status:', statusData.status);

                        if (statusData.status === 'COMPLETED' || statusData.status === 'COMPLETED_WITH_ERRORS') {
                            analysisData = statusData;
                            logger.log('→ Project analysis completed!');
                            break;
                        } else if (statusData.status === 'FAILED') {
                            const reason = statusData.error_message || statusData.error || statusData.detail || '';
                            throw new Error('Project analysis failed on server' + (reason ? ': ' + reason : ''));
                        }
                    } catch (pollError: any) {
                        const is404 = (pollError?.response?.status === 404) || String(pollError?.message).includes('404');
                        if (is404 && attempt < 3) continue;
                        throw pollError;
                    }
                }

                if (!analysisData) {
                    throw new Error('Project analysis timed out. Please try again.');
                }

                // Step 4: Get project class diagram
                const diagramData = await UnifiedApiService.getProjectClassDiagram(payload.projectId);
                logger.log('→ Project class diagram fetched:', diagramData);

                // Close modal
                setShowCodeModal(false);
                setCodeProject(null);

                // Step 5: Navigate to Class Diagram page
                navigate('/diagram', {
                    state: {
                        projectId: payload.projectId,
                        codeName: payload.codeName || payload.fileName,
                        fileName: payload.fileName,
                        isProjectDiagram: true,
                        analysisIds: analysisData.analysis_ids || [],
                        diagram: convertProjectDiagramToDiagramFormat(diagramData.project_class_diagram),
                    }
                });

                showAlert({
                    type: 'success',
                    title: 'Success',
                    message: `File analyzed successfully! Found ${diagramData.total_classes || 0} classes.`
                });

                return;
            }
        } catch (err: any) {
            const errorMessage = formatApiError(err);
            setCodeError(errorMessage);
            logger.error('→ Error in handleCodeSubmit:', err);
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

    const handleViewCodes = (project: Project) => {
        navigate(`/dashboard/projects/${project.id}/codes`);
    };

    const handleViewDocuments = (project: Project) => {
        navigate(`/dashboard/projects/${project.id}/documents`);
    };

    const handleViewProjectFiles = (project: Project) => {
        navigate(`/dashboard/projects/${project.id}/tree`);
    };


    const handleCreateProject = () => {
        setShowCreateProjectModal(true);
    };

    const handleCreateProjectSubmit = async (data: { title: string; description: string }) => {
        try {
            logger.log('📝 Creating project:', data.title);
            const newProject = await apiService.projects.create(data);
            setProjects([...projects, newProject]);

            // 🔄 Refetch notifications after successful creation
            try {
                logger.log('🔄 Refetching notifications after project creation...');
                if (user?.email) {
                    const notificationResponse = await apiService.notifications.getNotifications({
                        user_email: user.email
                    });
                    logger.log('📥 Notifications after creation:', notificationResponse);

                    // Dispatch event to notify NotificationBell component
                    window.dispatchEvent(new CustomEvent('notification-update', {
                        detail: {
                            type: 'project-created',
                            projectId: newProject.id,
                            projectName: newProject.title,
                            timestamp: new Date().toISOString()
                        }
                    }));

                    logger.log('✅ Dispatched notification-update event for project creation');
                }
            } catch (notifError) {
                logger.error('❌ Failed to refetch notifications after creation:', notifError);
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
        if (!bytes) return '—';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const handleDownloadFile = async (file: any) => {
        try {
            const res = await apiClient.get(`/api/analysis/download-generated-file/${file._id}/`, {
                responseType: 'blob',
            });
            const blob = res.data as Blob;
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name || file.filename || 'file';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            logger.error('Download error:', err);
        }
    };

    const handleViewFile = async (file: any) => {
        try {
            const res = await apiClient.get(`/api/analysis/download-generated-file/${file._id}/`, {
                responseType: 'blob',
            });
            const blob = res.data as Blob;
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
            setTimeout(() => URL.revokeObjectURL(url), 10000);
        } catch (err) {
            logger.error('View error:', err);
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

                            {/* Right column: spacer → icons → spacer → button → spacer */}
                            {/* Right column: spacer → icons → spacer → button → spacer */}
                            <div className="hero-right-col">
                                {/* Top spacer */}
                                <div className="hero-spacer hero-spacer-top" />

                                {/* Staircase icons */}
                                <div className="hero-feature-icons">
                                    {/* 1: Folder (amber) — bottom-left */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M1.5 7a1.2 1.2 0 0 1 1.2-1.2h7.5l1.5 1.8a.8.8 0 0 0 .6.3h11.5a1.2 1.2 0 0 1 1.2 1.2v11a1.2 1.2 0 0 1-1.2 1.2H2.7a1.2 1.2 0 0 1-1.2-1.2V7z" opacity="0.3"/>
                                            <path d="M3 10.5a1.2 1.2 0 0 1 1.2-1.2h7.5l1.5 1.8a.8.8 0 0 0 .6.3h11.5a1.2 1.2 0 0 1 1.2 1.2v8a1.2 1.2 0 0 1-1.2 1.2H4.2A1.2 1.2 0 0 1 3 22.6v-12.1z"/>
                                            <rect x="9" y="14.5" width="7" height="7" rx="0.8" opacity="0.45"/>
                                            <line x1="11" y1="17" x2="14" y2="17" opacity="0.35"/>
                                            <line x1="11" y1="19" x2="13.5" y2="19" opacity="0.35"/>
                                        </svg>
                                    </div>
                                    {/* 2: UML Class (blue) — middle */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="0.5" y="0.5" width="10" height="9" rx="1.2" fill="rgba(56,189,248,0.08)"/>
                                            <line x1="0.5" y1="3.5" x2="10.5" y2="3.5"/>
                                            <text x="5.5" y="2.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">A</text>
                                            <line x1="2" y1="5.8" x2="9" y2="5.8" opacity="0.3"/>
                                            <line x1="2" y1="7.5" x2="7.5" y2="7.5" opacity="0.3"/>
                                            <rect x="17.5" y="0.5" width="10" height="9" rx="1.2" fill="rgba(56,189,248,0.08)"/>
                                            <line x1="17.5" y1="3.5" x2="27.5" y2="3.5"/>
                                            <text x="22.5" y="2.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">B</text>
                                            <line x1="19" y1="5.8" x2="26" y2="5.8" opacity="0.3"/>
                                            <line x1="19" y1="7.5" x2="24" y2="7.5" opacity="0.3"/>
                                            <rect x="7" y="16" width="14" height="11" rx="1.2" fill="rgba(56,189,248,0.08)"/>
                                            <line x1="7" y1="19.5" x2="21" y2="19.5"/>
                                            <text x="14" y="18.8" textAnchor="middle" fill="rgba(56,189,248,0.8)" fontSize="2.5" fontFamily="monospace" stroke="none">C</text>
                                            <line x1="9" y1="22" x2="19" y2="22" opacity="0.3"/>
                                            <line x1="9" y1="24" x2="17" y2="24" opacity="0.3"/>
                                            <line x1="5.5" y1="9.5" x2="10" y2="16" opacity="0.45"/>
                                            <polygon points="10,16 9,14.5 10.8,14.8" fill="rgba(56,189,248,0.45)" stroke="none"/>
                                            <line x1="22.5" y1="9.5" x2="18" y2="16" opacity="0.45"/>
                                            <polygon points="18,16 19,14.5 17.2,14.8" fill="rgba(56,189,248,0.45)" stroke="none"/>
                                            <line x1="10.5" y1="5" x2="17.5" y2="5" opacity="0.25" strokeDasharray="1.2 1"/>
                                        </svg>
                                    </div>
                                    {/* 3: Explanation (green) — top-right */}
                                    <div className="hero-st-icon">
                                        <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="1" y="0.5" width="26" height="27" rx="2.5" fill="rgba(52,211,153,0.05)"/>
                                            <rect x="1" y="0.5" width="26" height="6" rx="2.5" fill="rgba(52,211,153,0.1)"/>
                                            <line x1="1" y1="6.5" x2="27" y2="6.5" opacity="0.3"/>
                                            <circle cx="4.5" cy="3.5" r="0.8" fill="rgba(52,211,153,0.5)" stroke="none"/>
                                            <circle cx="7.2" cy="3.5" r="0.8" fill="rgba(52,211,153,0.3)" stroke="none"/>
                                            <line x1="10" y1="3.5" x2="22" y2="3.5" opacity="0.35"/>
                                            <rect x="3.5" y="8.5" width="7" height="3.5" rx="0.8" fill="rgba(52,211,153,0.12)" stroke="rgba(52,211,153,0.3)" strokeWidth="0.7"/>
                                            <text x="7" y="11.3" textAnchor="middle" fill="rgba(52,211,153,0.7)" fontSize="2.2" fontFamily="monospace" fontWeight="600" stroke="none">HIGH</text>
                                            <circle cx="3" cy="15" r="0.5" fill="rgba(52,211,153,0.45)" stroke="none"/>
                                            <line x1="4.5" y1="15" x2="24" y2="15" opacity="0.2"/>
                                            <circle cx="3" cy="17.5" r="0.5" fill="rgba(52,211,153,0.35)" stroke="none"/>
                                            <line x1="4.5" y1="17.5" x2="21" y2="17.5" opacity="0.2"/>
                                            <circle cx="3" cy="20" r="0.5" fill="rgba(52,211,153,0.35)" stroke="none"/>
                                            <line x1="4.5" y1="20" x2="23" y2="20" opacity="0.2"/>
                                            <line x1="3" y1="22" x2="24" y2="22" opacity="0.1" strokeDasharray="1.2 1"/>
                                            <circle cx="3" cy="24" r="0.5" fill="rgba(52,211,153,0.3)" stroke="none"/>
                                            <line x1="4.5" y1="24" x2="19" y2="24" opacity="0.15"/>
                                            <circle cx="3" cy="26" r="0.5" fill="rgba(52,211,153,0.2)" stroke="none"/>
                                            <line x1="4.5" y1="26" x2="22" y2="26" opacity="0.15"/>
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
                                                            onClick={() => handleViewCodes(project)}
                                                            className="action-btn action-view"
                                                            title={language === 'ar' ? 'عرض الأكواد' : 'View Codes'}
                                                        >
                                                            <Code size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleViewDocuments(project)}
                                                            className="action-btn action-view"
                                                            title={language === 'ar' ? 'عرض المستندات' : 'View Documents'}
                                                        >
                                                            <FileText size={16} />
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

        if (activeAction === 'conflict') {
            return (
                <div className="conflict-detection-section" style={{ padding: '2rem' }}>
                    <div style={{ marginBottom: '2rem' }}>
                        <h1 className="section-title">
                            {language === 'ar' ? 'كشف التناقضات' : 'Conflict Detection'}
                        </h1>
                        <p className="section-subtitle">
                            {language === 'ar'
                                ? 'قارن الأكواد والتوثيق واكتشف التناقضات والاختلافات'
                                : 'Compare code and documentation to detect conflicts and differences'
                            }
                        </p>
                    </div>

                    {!activeConflictType ? (
                        <div>
                            <SimpleConflictSelector
                                onSelect={(type) => {
                                    setActiveConflictType(type);
                                }}
                            />
                        </div>
                    ) : (
                        <div>
                            <button
                                type="button"
                                onClick={() => setActiveConflictType(null)}
                                style={{
                                    background: 'rgba(255,255,255,0.2)',
                                    border: '1px solid rgba(255,255,255,0.3)',
                                    color: isDarkMode ? 'white' : '#1f2937',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    marginBottom: '1rem'
                                }}
                            >
                                ← {language === 'ar' ? 'العودة للخيارات' : 'Back to Options'}
                            </button>
                            {activeConflictType === 'code_vs_code' && (
                                <CodeVsCode
                                    isOpen={true}
                                    onClose={() => setActiveConflictType(null)}
                                />
                            )}
                            {activeConflictType === 'code_vs_doc' && (
                                <CodeVsDoc
                                    isOpen={true}
                                    onClose={() => setActiveConflictType(null)}
                                />
                            )}
                            {activeConflictType === 'full_analysis' && (
                                <FullAnalysis
                                    isOpen={true}
                                    onClose={() => setActiveConflictType(null)}
                                />
                            )}
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
                    <button
                        onClick={() => setActiveAction('conflict')}
                        className={`nav-item ${activeAction === 'conflict' ? 'active' : ''}`}
                    >
                        <GitCompare size={20} />
                        <span>{language === 'ar' ? 'كشف التناقضات' : 'Conflict Detection'}</span>
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
                    isDarkMode={isDarkMode}
                />
            )}

            {showProfileModal && (
                <ProfileModal
                    isOpen={showProfileModal}
                    onClose={() => setShowProfileModal(false)}
                    user={user}
                    onSave={(data: any) => {
                        logger.log('Profile updated:', data);
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
