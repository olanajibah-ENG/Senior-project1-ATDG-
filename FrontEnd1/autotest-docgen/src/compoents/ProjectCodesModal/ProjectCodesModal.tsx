import React from 'react';
import { X, Code, Calendar, User, FileText, Download } from 'lucide-react';
import type { ProjectCode } from '../../services/api.service';

interface ProjectCodesModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
    codes: ProjectCode[];
    isLoading: boolean;
}

const ProjectCodesModal: React.FC<ProjectCodesModalProps> = ({
    isOpen,
    onClose,
    projectName,
    codes,
    isLoading
}) => {
    if (!isOpen) return null;

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getLanguageIcon = (language: string) => {
        switch (language?.toLowerCase()) {
            case 'python':
                return '🐍';
            case 'java':
                return '☕';
            case 'javascript':
            case 'js':
                return '🟨';
            case 'typescript':
            case 'ts':
                return '🔷';
            default:
                return '📄';
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
                <div className="modal-header">
                    <h2 className="modal-title">
                        <Code size={20} style={{ marginRight: '8px' }} />
                        Project Codes - {projectName}
                    </h2>
                    <button className="modal-close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="modal-body">
                    {isLoading ? (
                        <div className="loading-state" style={{ textAlign: 'center', padding: '40px' }}>
                            <div className="spinner"></div>
                            <p>Loading codes...</p>
                        </div>
                    ) : codes.length === 0 ? (
                        <div className="empty-state" style={{ textAlign: 'center', padding: '40px' }}>
                            <Code size={64} style={{ opacity: 0.3 }} />
                            <h3>No codes uploaded yet</h3>
                            <p>Start by adding some code files to this project.</p>
                        </div>
                    ) : (
                        <div className="codes-list">
                            {codes.map((code, index) => (
                                <div key={code.id || index} className="code-item" style={{
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '8px',
                                    padding: '16px',
                                    marginBottom: '12px',
                                    backgroundColor: '#f9f9f9'
                                }}>
                                    <div className="code-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                        <div className="code-info" style={{ display: 'flex', alignItems: 'center' }}>
                                            <span style={{ fontSize: '24px', marginRight: '12px' }}>
                                                {getLanguageIcon(code.language || 'unknown')}
                                            </span>
                                            <div>
                                                <h4 style={{ margin: '0', fontSize: '16px', fontWeight: '600' }}>
                                                    {code.code_name || `Code ${index + 1}`}
                                                </h4>
                                                <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>
                                                    {code.file_name || 'Unknown file'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="code-meta" style={{ textAlign: 'right', fontSize: '12px', color: '#666' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                                                <Calendar size={12} style={{ marginRight: '4px' }} />
                                                {code.created_at ? formatDate(code.created_at) : 'Unknown date'}
                                            </div>
                                            {code.language && (
                                                <div style={{ backgroundColor: '#e3f2fd', color: '#1976d2', padding: '2px 8px', borderRadius: '12px', fontSize: '11px' }}>
                                                    {code.language.toUpperCase()}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    {code.version && (
                                        <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                                            Version: {code.version}
                                        </div>
                                    )}
                                    
                                    <div className="code-actions" style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                                        <button 
                                            className="action-btn action-view" 
                                            style={{ 
                                                backgroundColor: '#2196f3', 
                                                color: 'white', 
                                                border: 'none', 
                                                padding: '6px 12px', 
                                                borderRadius: '4px', 
                                                fontSize: '12px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            <FileText size={12} style={{ marginRight: '4px' }} />
                                            View Code
                                        </button>
                                        <button 
                                            className="action-btn action-download" 
                                            style={{ 
                                                backgroundColor: '#4caf50', 
                                                color: 'white', 
                                                border: 'none', 
                                                padding: '6px 12px', 
                                                borderRadius: '4px', 
                                                fontSize: '12px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            <Download size={12} style={{ marginRight: '4px' }} />
                                            Download
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button className="btn-secondary" onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProjectCodesModal;
