import React, { useState } from 'react';
import { Edit, X, AlertCircle, CheckCircle } from 'lucide-react';
import { type Project, type UpdateProjectData } from '../../services/api.service';

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

export default EditProjectForm;
