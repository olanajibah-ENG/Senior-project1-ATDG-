import React from 'react';
import LoadingSpinner from './LoadingSpinner';
import './LoadingSpinner.css';

interface AnalysisOverlayProps {
  message?: string;
}

const AnalysisOverlay: React.FC<AnalysisOverlayProps> = ({ message }) => {
  return (
    <div className="analysis-overlay">
      <div className="analysis-overlay-content">
        <LoadingSpinner size="small" message={message ?? 'Processing code, please wait...'} />
      </div>
    </div>
  );
};

export default AnalysisOverlay;




