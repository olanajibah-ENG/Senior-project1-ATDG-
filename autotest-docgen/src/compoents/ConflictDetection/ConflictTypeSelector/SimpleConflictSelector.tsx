import React from 'react';
import { GitCompare, FileText, Star, ArrowRight } from 'lucide-react';
import type { ConflictType } from './ConflictTypeSelector';
import './SimpleConflictSelector.css';
import '../shared/unified-dark-purple-theme.css';

interface Props {
  onSelect: (type: ConflictType) => void;
}

const options = [
  {
    id: 'code_vs_code' as ConflictType,
    icon: GitCompare,
    iconColor: '#4c1d95',
    iconBg: 'rgba(76,29,149,0.1)',
    title: 'Code vs Code',
    description: 'Compare two versions of the same file — detect structural, logical changes, and Class Diagram differences',
    badges: ['Structure Change', 'Class Diagram', 'Logic'],
    badgeColors: ['#ef4444', '#4c1d95', '#f59e0b'],
    recommended: false,
  },
  {
    id: 'code_vs_doc' as ConflictType,
    icon: FileText,
    iconColor: '#10b981',
    iconBg: 'rgba(16,185,129,0.1)',
    title: 'Code vs Documentation',
    description: 'Compare code with its documentation — detect conflicts between actual implementation and documented behavior',
    badges: ['Wrong Docs', 'Missing', 'Coverage'],
    badgeColors: ['#ef4444', '#f59e0b', '#10b981'],
    recommended: false,
  },
  {
    id: 'full_analysis' as ConflictType,
    icon: Star,
    iconColor: '#4c1d95',
    iconBg: 'rgba(76,29,149,0.1)',
    title: 'Full Analysis',
    description: 'Comprehensive analysis — Code vs Code + Code vs Doc together with automatic migration guide and complete report',
    badges: ['Complete', 'Migration Guide', 'PDF Report'],
    badgeColors: ['#4c1d95', '#6d28d9', '#10b981'],
    recommended: true,
  },
];

const SimpleConflictSelector: React.FC<Props> = ({ onSelect }) => {
  return (
    <div className="scs-container">
      <div className="scs-title-wrapper">
        <h1 className="scs-main-title">Conflict Detection</h1>
        <p className="scs-subtitle-text">Choose the analysis type that suits your needs</p>
      </div>

      <div className="scs-legend">
        <span className="scs-legend-item"><span className="scs-dot" style={{ background: '#10b981' }} />Added</span>
        <span className="scs-legend-item"><span className="scs-dot" style={{ background: '#ef4444' }} />Removed</span>
        <span className="scs-legend-item"><span className="scs-dot" style={{ background: '#f59e0b' }} />Modified</span>
      </div>

      <div className="scs-cards">
        {options.map(opt => {
          const Icon = opt.icon;
          return (
            <div
              key={opt.id}
              className={`scs-card ${opt.recommended ? 'recommended' : ''}`}
              onClick={() => onSelect(opt.id)}
            >
              {opt.recommended && (
                <span className="scs-recommended-tag">Recommended</span>
              )}

              <div className="scs-card-icon" style={{ background: opt.iconBg }}>
                <Icon size={26} color={opt.iconColor} />
              </div>

              <h3 className="scs-card-title">{opt.title}</h3>
              <p className="scs-card-desc">{opt.description}</p>

              <div className="scs-card-badges">
                {opt.badges.map((b, i) => (
                  <span
                    key={b}
                    className="scs-badge"
                    style={{ color: opt.badgeColors[i], borderColor: opt.badgeColors[i] + '55', background: opt.badgeColors[i] + '18' }}
                  >
                    {b}
                  </span>
                ))}
              </div>

              <button className="scs-card-btn">
                Start Analysis <ArrowRight size={15} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SimpleConflictSelector;
