import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { User, FileText, Edit, Trash2, Pin } from 'lucide-react';
import type { Project, ProjectDocumentation } from '../../services/api.service';
import { ApiService } from '../../services/api.service';
import LoadingSpinner from './LoadingSpinner';
import { useLanguage } from '../../context/LanguageContext';
import './ProjectList.css';

interface ProjectsListProps {
    projects: Project[] | null;
    isLoading: boolean;
    error: string | null;
    onEdit: (projectId: string) => void;
    onDelete: (projectId: string) => void;
    onAddCode: (projectId: string) => void;
    onOpenFile?: (projectId: string, fileName: string, fileType: 'code' | 'doc') => void;
    onViewFiles?: (projectId: string) => void;
}

const ProjectsList: React.FC<ProjectsListProps> = ({
    projects,
    isLoading,
    error,
    onEdit,
    onDelete,
    onAddCode,
    onOpenFile,
    onViewFiles,
}) => {
    const { t } = useLanguage();
    const [projectDocumentation, setProjectDocumentation] = useState<Record<string, ProjectDocumentation[]>>({});
    const [loadingDocs, setLoadingDocs] = useState<Record<string, boolean>>({});

    const apiService = new ApiService();
    const fetchedProjectsRef = useRef<Set<string>>(new Set());

    // Fetch project documentation from API
    const fetchProjectDocumentation = useCallback(async (projectId: string) => {
        if (fetchedProjectsRef.current.has(`doc-${projectId}`)) {
            return;
        }

        fetchedProjectsRef.current.add(`doc-${projectId}`);
        setLoadingDocs(prev => ({ ...prev, [projectId]: true }));

        try {
            console.log(`Fetching documentation for project: ${projectId}`);
            const docs = await apiService.getProjectDocumentation(projectId);
            console.log(`Documentation fetched:`, docs);
            setProjectDocumentation(prev => ({ ...prev, [projectId]: docs }));
        } catch (error) {
            console.error('Failed to fetch project documentation:', error);
            // Add mock data for testing
            const mockDocs = [
                { id: '1', name: 'Class Diagram - Main System', type: 'class_diagram' as const, created_at: new Date().toISOString() },
                { id: '2', name: 'Logic Explanation - User Authentication', type: 'logic_explanation' as const, created_at: new Date().toISOString() },
                { id: '3', name: 'Class Diagram - Database Models', type: 'class_diagram' as const, created_at: new Date().toISOString() },
                { id: '4', name: 'Logic Explanation - Payment Processing', type: 'logic_explanation' as const, created_at: new Date().toISOString() }
            ];
            setProjectDocumentation(prev => ({ ...prev, [projectId]: mockDocs }));
        } finally {
            setLoadingDocs(prev => ({ ...prev, [projectId]: false }));
        }
    }, [apiService]);

    // Memoize project IDs to prevent unnecessary re-renders
    const projectIds = useMemo(() => {
        return projects ? projects.map(p => p.id).sort().join(',') : '';
    }, [projects]);

    // Load data when projects change - use project IDs string to prevent loops
    useEffect(() => {
        if (projects && projects.length > 0) {
            // Reset ref for new projects
            const currentProjectIds = new Set(projects.map(p => p.id));
            const toRemove: string[] = [];
            fetchedProjectsRef.current.forEach(key => {
                const projectId = key.replace(/^(code|doc)-/, '');
                if (!currentProjectIds.has(projectId)) {
                    toRemove.push(key);
                }
            });
            toRemove.forEach(key => fetchedProjectsRef.current.delete(key));

            // Fetch for all current projects
            projects.forEach(project => {
                fetchProjectDocumentation(project.id);
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectIds]); // Only depend on projectIds string

    const handleViewDocuments = (projectId: string) => {
        if (onOpenFile) {
            // Show all documents for this project
            const docs = projectDocumentation[projectId] || [];
            if (docs.length === 0) {
                onOpenFile(projectId, 'No documents available', 'doc');
            } else {
                // You could open a modal or navigate to documents page
                console.log(`Viewing ${docs.length} documents for project: ${projectId}`);
                onOpenFile(projectId, docs.map(doc => doc.name).join(', '), 'doc');
            }
        }
    };

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
                <LoadingSpinner size="large" message={t('projects.loading')} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-message" style={{ padding: '20px', margin: '20px 0' }}>
                <strong>{t('projects.error')}:</strong> {error}
            </div>
        );
    }

    if (!projects || projects.length === 0) {
        return (
            <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: 'var(--secondary-color)'
            }}>
                <h3 style={{ marginBottom: '10px', color: 'var(--text-color)' }}>{t('projects.no_projects')}</h3>
                <p>{t('projects.no_projects_message')}</p>
            </div>
        );
    }

    return (
        <div className="projects-list-container">
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px'
            }}>
                <h2 style={{ margin: 0, color: 'var(--text-color)' }}>
                    {t('projects.your_projects')} ({projects.length})
                </h2>
            </div>

            <div className="projects-table-wrapper saas-card">
                <table className="projects-table saas-table">
                    <thead>
                        <tr>
                            <th>{t('project.title.label')}</th>
                            <th>{t('project.description.label')}</th>
                            <th>{t('projects.owner')}</th>
                            <th>{t('projects.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {projects.map(project => {
                            return (
                                <tr key={project.id}>
                                    {/* Column 1: Title */}
                                    <td className="project-title-cell">
                                        <strong>{project.title}</strong>
                                    </td>
                                    {/* Column 2: Description */}
                                    <td className="project-description-cell">
                                        {project.description || <em style={{ color: 'var(--text-muted)' }}>{t('projects.no_description')}</em>}
                                    </td>
                                    {/* Column 3: Owner */}
                                    <td className="project-owner-cell">
                                        <User size={14} style={{ marginRight: '5px', verticalAlign: 'middle' }} />
                                        {project.username || `User ${project.user}`}
                                    </td>
                                    {/* Column 4: Actions */}
                                    <td className="project-actions-cell">
                                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'center' }}>
                                            <button
                                                onClick={() => {
                                                    console.log('📌 Pin button clicked in ProjectList for project:', project.id);
                                                    onAddCode(project.id);
                                                }}
                                                title={t('projects.add_code')}
                                                className="saas-icon-btn"
                                                style={{ color: 'var(--saas-blue)', borderColor: 'rgba(0, 123, 255, 0.2)' }}
                                            >
                                                <Pin size={14} />
                                            </button>
                                            <button
                                                onClick={() => onViewFiles ? onViewFiles(project.id) : handleViewDocuments(project.id)}
                                                title="View Code Files"
                                                className="saas-icon-btn"
                                                style={{ color: 'var(--saas-green)', borderColor: 'rgba(40, 167, 69, 0.2)' }}
                                                disabled={loadingDocs[project.id]}
                                            >
                                                {loadingDocs[project.id] ? (
                                                    <div className="spinner" style={{ width: '14px', height: '14px', border: '2px solid transparent', borderTop: '2px solid currentColor', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                                                ) : (
                                                    <FileText size={14} />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => onEdit(project.id)}
                                                title={t('projects.edit')}
                                                className="saas-icon-btn saas-icon-btn-edit"
                                            >
                                                <Edit size={14} />
                                            </button>
                                            <button
                                                onClick={() => onDelete(project.id)}
                                                title={t('projects.delete')}
                                                className="saas-icon-btn saas-icon-btn-delete"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ProjectsList;