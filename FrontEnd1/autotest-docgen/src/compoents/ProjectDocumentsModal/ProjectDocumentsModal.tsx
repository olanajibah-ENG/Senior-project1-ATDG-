import React from 'react';
import { X, File, Eye, Calendar, User } from 'lucide-react';
import type { ProjectDocumentation } from '../../services/api.service';

interface ProjectDocumentsModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
    documents: ProjectDocumentation[];
    isLoading: boolean;
    onDocumentClick?: (documentId: string, documentName: string) => void;
}

const ProjectDocumentsModal: React.FC<ProjectDocumentsModalProps> = ({
    isOpen,
    onClose,
    projectName,
    documents,
    isLoading,
    onDocumentClick
}) => {
    if (!isOpen) return null;

    const handleDocumentClick = (doc: ProjectDocumentation) => {
        if (onDocumentClick) {
            onDocumentClick(doc.id, doc.name);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getDocumentIcon = (type: string) => {
        switch (type) {
            case 'class_diagram':
                return '📊';
            case 'logic_explanation':
                return '📝';
            case 'documentation':
                return '📄';
            default:
                return '📁';
        }
    };

    const getDocumentTypeLabel = (type: string) => {
        switch (type) {
            case 'class_diagram':
                return 'Class Diagram';
            case 'logic_explanation':
                return 'Logic Explanation';
            case 'documentation':
                return 'Documentation';
            default:
                return 'Document';
        }
    };

    return (
        <div
            className="modal-overlay"
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                backdropFilter: 'blur(4px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                animation: 'fadeIn 0.3s ease-out'
            }}
            onClick={onClose}
        >
            <div
                className="saas-modal"
                onClick={(e) => e.stopPropagation()}
                style={{
                    maxWidth: '800px',
                    width: '90%',
                    maxHeight: '80vh'
                }}
            >
                {/* Modal Header */}
                <div className="saas-modal-header">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <h2 className="saas-modal-title">Project Documents</h2>
                            <p style={{
                                margin: 'var(--space-sm) 0 0 0',
                                color: 'var(--text-secondary)',
                                fontSize: '0.875rem'
                            }}>
                                {projectName} • {documents.length} documents
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="saas-icon-btn"
                            style={{
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--text-muted)'
                            }}
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Modal Body */}
                <div className="saas-modal-body">
                    {isLoading ? (
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: 'var(--space-3xl)'
                        }}>
                            <div className="saas-spinner"></div>
                            <p style={{
                                marginTop: 'var(--space-lg)',
                                color: 'var(--text-secondary)',
                                fontSize: '0.875rem'
                            }}>
                                Loading documents...
                            </p>
                        </div>
                    ) : documents.length === 0 ? (
                        <div style={{
                            textAlign: 'center',
                            padding: 'var(--space-3xl)',
                            color: 'var(--text-muted)'
                        }}>
                            <File size={48} style={{ marginBottom: 'var(--space-lg)', opacity: 0.5 }} />
                            <h3 style={{
                                fontSize: '1.125rem',
                                fontWeight: '600',
                                marginBottom: 'var(--space-sm)',
                                color: 'var(--text-secondary)'
                            }}>
                                No Documents Found
                            </h3>
                            <p style={{ fontSize: '0.875rem' }}>
                                This project doesn't have any generated documents yet.
                            </p>
                        </div>
                    ) : (
                        <div className="documents-grid" style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                            gap: 'var(--space-lg)'
                        }}>
                            {documents.map((doc, index) => (
                                <div
                                    key={doc.id}
                                    className="document-card saas-card"
                                    style={{
                                        cursor: 'pointer',
                                        padding: 'var(--space-lg)',
                                        animation: `slideUp 0.4s ease-out ${index * 0.1}s both`
                                    }}
                                    onClick={() => handleDocumentClick(doc)}
                                >
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
                                        <div style={{
                                            fontSize: '2rem',
                                            lineHeight: 1,
                                            flexShrink: 0
                                        }}>
                                            {getDocumentIcon(doc.type)}
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <h4 style={{
                                                fontSize: '0.875rem',
                                                fontWeight: '600',
                                                margin: '0 0 var(--space-xs) 0',
                                                color: 'var(--text-primary)',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap'
                                            }}>
                                                {doc.name}
                                            </h4>
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 'var(--space-sm)',
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)',
                                                marginBottom: 'var(--space-sm)'
                                            }}>
                                                <span className="saas-badge saas-badge-primary" style={{
                                                    fontSize: '0.625rem',
                                                    padding: '2px 6px'
                                                }}>
                                                    {getDocumentTypeLabel(doc.type)}
                                                </span>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                                                    <Calendar size={10} />
                                                    {formatDate(doc.created_at)}
                                                </span>
                                            </div>
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 'var(--space-sm)',
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)'
                                            }}>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                                                    <User size={10} />
                                                    Generated
                                                </span>
                                                <span>•</span>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                                                    <Eye size={10} />
                                                    View
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Modal Footer */}
                <div className="saas-modal-footer">
                    <button
                        onClick={onClose}
                        className="saas-btn saas-btn-secondary"
                    >
                        Close
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .document-card {
                    transition: all var(--transition-normal);
                }

                .document-card:hover {
                    transform: translateY(-2px);
                    box-shadow: var(--shadow-xl);
                }

                .documents-grid {
                    max-height: 400px;
                    overflow-y: auto;
                    padding-right: var(--space-sm);
                }

                .documents-grid::-webkit-scrollbar {
                    width: 6px;
                }

                .documents-grid::-webkit-scrollbar-track {
                    background: var(--border-light);
                    border-radius: 3px;
                }

                .documents-grid::-webkit-scrollbar-thumb {
                    background: var(--gradient-primary);
                    border-radius: 3px;
                }
            `}</style>
        </div>
    );
};

export default ProjectDocumentsModal;
