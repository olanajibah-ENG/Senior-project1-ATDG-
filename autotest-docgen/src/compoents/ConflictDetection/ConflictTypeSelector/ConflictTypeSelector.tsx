import React from 'react';
import { GitCompare, FileText, Star, X, ArrowRight, Sun, Moon } from 'lucide-react';
import './ConflictTypeSelector.css';

export type ConflictType = 'code_vs_code' | 'code_vs_doc' | 'full_analysis';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (type: ConflictType) => void;
  isDark?: boolean;
  onToggleTheme?: () => void;
}

const options = [
  {
    id: 'code_vs_code' as ConflictType,
    icon: GitCompare,
    iconColor: '#667eea',
    iconBg: 'rgba(102,126,234,0.15)',
    title: 'Code vs Code',
    description: 'Compare two versions of the same file — detect structural, logical changes, and Class Diagram differences',
    badges: ['Structure Change', 'Class Diagram', 'Logic'],
    badgeColors: ['#ef4444', '#667eea', '#f59e0b'],
    recommended: false,
  },
  {
    id: 'code_vs_doc' as ConflictType,
    icon: FileText,
    iconColor: '#10b981',
    iconBg: 'rgba(16,185,129,0.15)',
    title: 'Code vs Documentation',
    description: 'Compare code with its documentation — detect conflicts between actual implementation and documented behavior',
    badges: ['Wrong Docs', 'Missing', 'Coverage'],
    badgeColors: ['#ef4444', '#f59e0b', '#10b981'],
    recommended: false,
  },
  {
    id: 'full_analysis' as ConflictType,
    icon: Star,
    iconColor: '#a855f7',
    iconBg: 'rgba(168,85,247,0.15)',
    title: 'Full Analysis',
    description: 'Comprehensive analysis — Code vs Code + Code vs Doc together with automatic migration guide and complete report',
    badges: ['Complete', 'Migration Guide', 'PDF Report'],
    badgeColors: ['#a855f7', '#667eea', '#10b981'],
    recommended: true,
  },
];

const ConflictTypeSelector: React.FC<Props> = ({ isOpen, onClose, onSelect, isDark = true, onToggleTheme }) => {
  if (!isOpen) return null;

  return (
    <div className={`cts-overlay ${isDark ? 'cts-dark' : 'cts-light'}`} onClick={onClose}>
      <div className="cts-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="cts-header">
          <div className="cts-header-left">
            <div className="cts-header-icon">
              <GitCompare size={22} color="#fff" />
            </div>
            <div>
              <h2 className="cts-title">Conflict Detection</h2>
              <p className="cts-subtitle">Choose the analysis type that suits your needs</p>
            </div>
          </div>
          <div className="cts-header-actions">
            {onToggleTheme && (
              <button className="cts-theme-toggle" onClick={onToggleTheme} title="Toggle theme">
                {isDark ? <Sun size={16} /> : <Moon size={16} />}
              </button>
            )}
            <button className="cts-close" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="cts-legend">
          <span className="cts-legend-item">
            <span className="cts-dot" style={{ background: '#10b981' }} />
            Added
          </span>
          <span className="cts-legend-item">
            <span className="cts-dot" style={{ background: '#ef4444' }} />
            Removed
          </span>
          <span className="cts-legend-item">
            <span className="cts-dot" style={{ background: '#f59e0b' }} />
            Modified
          </span>
        </div>

        {/* Cards */}
        <div className="cts-cards">
          {options.map(opt => {
            const Icon = opt.icon;
            return (
              <div
                key={opt.id}
                className={`cts-card ${opt.recommended ? 'recommended' : ''}`}
                onClick={() => onSelect(opt.id)}
              >
                {opt.recommended && (
                  <span className="cts-recommended-tag">Recommended</span>
                )}

                <div className="cts-card-icon" style={{ background: opt.iconBg }}>
                  <Icon size={26} color={opt.iconColor} />
                </div>

                <h3 className="cts-card-title">{opt.title}</h3>
                <p className="cts-card-desc">{opt.description}</p>

                <div className="cts-card-badges">
                  {opt.badges.map((b, i) => (
                    <span
                      key={b}
                      className="cts-badge"
                      style={{ color: opt.badgeColors[i], borderColor: opt.badgeColors[i] + '55', background: opt.badgeColors[i] + '18' }}
                    >
                      {b}
                    </span>
                  ))}
                </div>

                <button className="cts-card-btn">
                  Start Analysis <ArrowRight size={15} />
                </button>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};

export default ConflictTypeSelector;
