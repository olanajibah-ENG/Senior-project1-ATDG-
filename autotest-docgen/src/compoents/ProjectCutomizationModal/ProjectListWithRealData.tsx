// ProjectListWithRealData.tsx
// Example of how to use real API data instead of mock data

import React, { useState, useEffect } from 'react';
import { FileCode, FileText, ExternalLink } from 'lucide-react';
import type { Project } from '../../services/api.service';
import FilesService, { type ProjectFile } from '../../services/files.service';

interface ProjectsListWithRealDataProps {
    projects: Project[] | null;
    isLoading: boolean;
    error: string | null;
    onOpenFile?: (projectId: string, fileName: string, fileType: 'code' | 'doc') => void;
}

const ProjectsListWithRealData: React.FC<ProjectsListWithRealDataProps> = ({
    projects,
    isLoading,
    error,
    onOpenFile,
}) => {
    // Store files for each project
    const [projectFiles, setProjectFiles] = useState<Record<string, {
        codeFiles: ProjectFile[];
        docFiles: ProjectFile[];
        loading: boolean;
        error: string | null;
    }>>({});

    // Load files for all projects
    useEffect(() => {
        if (!projects || projects.length === 0) return;

        const loadProjectFiles = async () => {
            const filesData: typeof projectFiles = {};

            // Initialize loading state for all projects
            projects.forEach(project => {
                filesData[project.id] = {
                    codeFiles: [],
                    docFiles: [],
                    loading: true,
                    error: null
                };
            });
            setProjectFiles(filesData);

            // Load files for each project
            for (const project of projects) {
                try {
                    const response = await FilesService.getProjectFiles(project.id);
                    filesData[project.id] = {
                        codeFiles: response.code_files,
                        docFiles: response.documentation_files,
                        loading: false,
                        error: null
                    };
                } catch (err) {
                    filesData[project.id] = {
                        codeFiles: [],
                        docFiles: [],
                        loading: false,
                        error: 'Failed to load files'
                    };
                }
            }

            setProjectFiles({ ...filesData });
        };

        loadProjectFiles();
    }, [projects]);

    const handleFileClick = async (projectId: string, file: ProjectFile) => {
        if (onOpenFile) {
            onOpenFile(projectId, file.name, file.type);
        } else {
            // Default behavior - load and display file content
            try {
                const content = await FilesService.getFileContent(projectId, file.id);
                console.log(`File content for ${file.name}:`, content);
                // You could open a modal here to display the content
            } catch (error) {
                console.error('Failed to load file content:', error);
            }
        }
    };

    const renderFilesList = (files: ProjectFile[], projectId: string, isLoading: boolean, error: string | null) => {
        if (isLoading) {
            return (
                <div className="files-loading">
                    <span style={{ color: 'var(--secondary-color)', fontStyle: 'italic' }}>
                        Loading files...
                    </span>
                </div>
            );
        }

        if (error) {
            return (
                <div className="files-error">
                    <span style={{ color: '#dc3545', fontStyle: 'italic', fontSize: '0.75rem' }}>
                        {error}
                    </span>
                </div>
            );
        }

        if (files.length === 0) {
            return (
                <span style={{ color: 'var(--secondary-color)', fontStyle: 'italic' }}>
                    No files
                </span>
            );
        }

        return (
            <div className="files-list">
                {files.map((file) => (
                    <button
                        key={file.id}
                        className="file-link"
                        onClick={() => handleFileClick(projectId, file)}
                        title={`Open ${file.name} (${(file.size / 1024).toFixed(1)} KB)`}
                    >
                        {file.type === 'code' ? (
                            <FileCode size={12} style={{ marginRight: '4px' }} />
                        ) : (
                            <FileText size={12} style={{ marginRight: '4px' }} />
                        )}
                        {file.name}
                        <ExternalLink size={10} style={{ marginLeft: '4px', opacity: 0.6 }} />
                    </button>
                ))}
            </div>
        );
    };

    if (isLoading) {
        return <div>Loading projects...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!projects || projects.length === 0) {
        return <div>No projects found</div>;
    }

    return (
        <div className="projects-table-wrapper">
            <table className="projects-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Description</th>
                        <th>Owner</th>
                        <th>Created</th>
                        <th>Code Files</th>
                        <th>Documentation</th>
                    </tr>
                </thead>
                <tbody>
                    {projects.map(project => {
                        const files = projectFiles[project.id] || {
                            codeFiles: [],
                            docFiles: [],
                            loading: true,
                            error: null
                        };
                        
                        return (
                            <tr key={project.id}>
                                <td className="project-title-cell">
                                    <strong>{project.title}</strong>
                                </td>
                                <td className="project-description-cell">
                                    {project.description || <em>No description</em>}
                                </td>
                                <td className="project-owner-cell">
                                    {project.username || `User ${project.user}`}
                                </td>
                                <td className="project-date-cell">
                                    {new Date(project.created_at).toLocaleDateString()}
                                </td>
                                <td className="project-files-cell">
                                    {renderFilesList(files.codeFiles, project.id, files.loading, files.error)}
                                </td>
                                <td className="project-docs-cell">
                                    {renderFilesList(files.docFiles, project.id, files.loading, files.error)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default ProjectsListWithRealData;