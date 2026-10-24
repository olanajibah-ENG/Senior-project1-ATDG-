import React, { useState } from 'react';
import { Plus, X, AlertCircle } from 'lucide-react';

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

export default CreateProjectForm;
