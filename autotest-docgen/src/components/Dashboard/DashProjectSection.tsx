import React, { useState } from 'react';
import { Eye, Download } from 'lucide-react';

// ── DashProjectSection — per-project card with Grid/List toggle ──────
const DashProjectSection: React.FC<{
    projectName: string;
    files: any[];
    onView: (f: any) => void;
    onDownload: (f: any) => void;
    isDark: boolean;
    lang: string;
}> = ({ projectName, files, onView, onDownload, isDark, lang }) => {
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    const fmt = (bytes: number) => {
        if (!bytes) return '—';
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
                            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                        </svg>
                        Grid
                    </button>
                    <button
                        className={`dash-view-btn${viewMode === 'list' ? ' active' : ''}`}
                        onClick={() => setViewMode('list')}
                        title="List"
                    >
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                            <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
                            <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
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
                                <th style={{ textAlign: 'right' }}>{lang === 'ar' ? 'إجراءات' : 'Actions'}</th>
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

export default DashProjectSection;
