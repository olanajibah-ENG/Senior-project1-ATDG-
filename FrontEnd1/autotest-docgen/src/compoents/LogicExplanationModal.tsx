import React, { useState, useEffect } from 'react';
import { Lightbulb, Users, Code, ArrowRight, X } from 'lucide-react';
import { type LogicExplanationLevel, type Project } from '../services/api.service';
import { useLanguage } from '../context/LanguageContext';
import './LogicExplanationModal.css';

interface LogicExplanationModalProps {
  project: Project;
  codeName: string;
  fileName: string;
  codeContent: string;
  isProcessing: boolean;
  apiError: string | null;
  onExplainLogic: (level: 'high_level' | 'low_level') => void;
  onClose: () => void;
}

const LogicExplanationModal: React.FC<LogicExplanationModalProps> = ({
  project,
  codeName,
  fileName,
  codeContent,
  isProcessing,
  apiError,
  onExplainLogic,
  onClose,
}) => {
  const { language, t } = useLanguage();
  const [levels, setLevels] = useState<LogicExplanationLevel[]>([]);
  const [selectedLevel, setSelectedLevel] = useState<'high_level' | 'low_level' | null>(null);
  const [isLoadingLevels, setIsLoadingLevels] = useState(true);

  useEffect(() => {
    // Use static levels - no API call needed
    setLevels([
      {
        id: 'high_level',
        name: language === 'ar' ? 'شرح بسيط' : 'Simple Explanation',
        description: language === 'ar' ? 'ماذا يفعل الكود؟' : 'What does the code do?',
        icon: '💡',
        suitable_for: language === 'ar' ? 'الجميع' : 'Everyone'
      },
      {
        id: 'low_level',
        name: language === 'ar' ? 'شرح مفصل' : 'Detailed Explanation',
        description: language === 'ar' ? 'كيف يعمل الكود بالتفصيل؟' : 'How does the code work in detail?',
        icon: '⚙️',
        suitable_for: language === 'ar' ? 'المطورين' : 'Developers'
      }
    ]);
    setIsLoadingLevels(false);
  }, [language]);

  const handleLevelSelect = (levelId: string) => {
    setSelectedLevel(levelId as 'high_level' | 'low_level');
  };

  const handleExplain = () => {
    if (selectedLevel) {
      onExplainLogic(selectedLevel);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
        <div className="logic-explanation-header">
          <div className="logic-explanation-title">
            <Lightbulb size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
            <h1>{t('logic.modal.title')}</h1>
          </div>
          <p className="logic-explanation-subtitle">
            {t('logic.modal.subtitle')}
          </p>
        </div>

        {(apiError) && (
          <div className="logic-explanation-error">
            <X size={20} />
            <div>
              <strong>خطأ:</strong>
              <p style={{ margin: '4px 0 0 0' }}>{apiError}</p>
            </div>
          </div>
        )}

        <div className="logic-explanation-content">
          <div className="code-info-section">
            <h3>{t('logic.modal.code_info')}</h3>
            <div className="code-info-card">
              <div className="code-info-item">
                <Code size={16} />
                <span><strong>{t('logic.modal.project')}:</strong> {project.title}</span>
              </div>
              <div className="code-info-item">
                <Code size={16} />
                <span><strong>{t('logic.modal.code_name')}:</strong> {codeName}</span>
              </div>
              <div className="code-info-item">
                <Code size={16} />
                <span><strong>{t('logic.modal.file')}:</strong> {fileName}</span>
              </div>
              <div className="code-info-item">
                <Code size={16} />
                <span><strong>{t('logic.modal.lines_count')}:</strong> {codeContent.split('\n').length}</span>
              </div>
            </div>
          </div>

          <div className="levels-section">
            <h3>{t('logic.modal.choose_level')}</h3>
            {isLoadingLevels ? (
              <div className="levels-loading">
                <div className="spinner"></div>
                <p>{t('logic.modal.loading_levels')}</p>
              </div>
            ) : (
              <div className="levels-grid">
                {levels.map((level) => (
                  <div
                    key={level.id}
                    className={`level-card ${selectedLevel === level.id ? 'selected' : ''}`}
                    onClick={() => handleLevelSelect(level.id)}
                  >
                    <div className="level-icon">
                      <span style={{ fontSize: '2rem' }}>{level.icon}</span>
                    </div>
                    <div className="level-content">
                      <h4>{level.name}</h4>
                      <p>{level.description}</p>
                      <div className="level-suitable">
                        <Users size={14} />
                        <span>مناسب لـ {level.suitable_for}</span>
                      </div>
                    </div>
                    <div className="level-radio">
                      <input
                        type="radio"
                        name="explanation-level"
                        value={level.id}
                        checked={selectedLevel === level.id}
                        onChange={() => handleLevelSelect(level.id)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="logic-explanation-actions">
          <button
            type="button"
            onClick={handleExplain}
            disabled={isProcessing || !selectedLevel || isLoadingLevels}
            className="logic-explanation-btn logic-explanation-btn-primary"
          >
            {isProcessing ? (
              <>
                <div className="button-spinner"></div>
                {t('logic.modal.explaining')}
              </>
            ) : (
              <>
                <Lightbulb size={20} style={{ marginRight: '8px' }} />
                {t('logic.modal.explain_logic')}
                <ArrowRight size={20} style={{ marginLeft: '8px' }} />
              </>
            )}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={isProcessing}
            className="logic-explanation-btn logic-explanation-btn-secondary"
          >
            <X size={20} style={{ marginRight: '8px' }} />
            {t('logic.modal.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogicExplanationModal;
